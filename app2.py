import streamlit as st
import openai
import requests
import pandas as pd
import json
from datetime import datetime
import time
import matplotlib.pyplot as plt
import seaborn as sns

# Set page configuration
st.set_page_config(
    page_title="FPL Assistant",
    page_icon="⚽",
    layout="wide",
)

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_team" not in st.session_state:
    st.session_state.user_team = None

# FPL API endpoints
BASE_URL = "https://fantasy.premierleague.com/api/"
BOOTSTRAP_URL = f"{BASE_URL}bootstrap-static/"
FIXTURES_URL = f"{BASE_URL}fixtures/"
PLAYER_URL = f"{BASE_URL}element-summary/"

# Cache the API responses to avoid repeated calls
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_fpl_data():
    """Fetch and return basic FPL data."""
    response = requests.get(BOOTSTRAP_URL)
    return response.json()

@st.cache_data(ttl=3600)
def get_fixtures_data():
    """Fetch and return fixtures data."""
    response = requests.get(FIXTURES_URL)
    return response.json()

@st.cache_data(ttl=3600)
def get_player_data(player_id):
    """Fetch and return detailed data for a specific player."""
    response = requests.get(f"{PLAYER_URL}{player_id}/")
    return response.json()

def get_current_gameweek(events_data):
    """Determine the current gameweek."""
    for event in events_data:
        if event['is_current']:
            return event['id']
    # If no current gameweek found, return the next one
    for event in events_data:
        if event['is_next']:
            return event['id']
    return 1  # Default to 1 if nothing found

def preprocess_player_data(data):
    """Transform raw FPL data into a more usable player dataframe."""
    players = data['elements']
    teams = {team['id']: team['name'] for team in data['teams']}
    positions = {pos['id']: pos['singular_name'] for pos in data['element_types']}
    
    player_df = pd.DataFrame(players)
    
    # Add team name and position
    player_df['team_name'] = player_df['team'].map(teams)
    player_df['position'] = player_df['element_type'].map(positions)
    
    # Calculate points per game and value (points per cost)
    player_df['value'] = player_df['total_points'] / player_df['now_cost']
    
    # Filter to only include players who have played
    active_players = player_df[player_df['minutes'] > 0].copy()
    
    return active_players

def get_player_recommendations(player_df, position=None, budget=None, count=5):
    """Get player recommendations based on position and budget constraints."""
    filtered_df = player_df.copy()
    
    if position:
        filtered_df = filtered_df[filtered_df['position'] == position]
    
    if budget:
        # Convert budget to FPL format (multiply by 10)
        budget_internal = float(budget) * 10
        filtered_df = filtered_df[filtered_df['now_cost'] <= budget_internal]
    
    # Sort by value (points per cost)
    filtered_df = filtered_df.sort_values('value', ascending=False)
    
    return filtered_df.head(count)

def analyze_user_team(team_ids, all_players):
    """Analyze the user's team and suggest improvements."""
    team_df = all_players[all_players['id'].isin(team_ids)].copy()
    
    # Calculate team metrics
    total_value = team_df['now_cost'].sum() / 10  # Convert to display format
    total_points = team_df['total_points'].sum()
    avg_minutes = team_df['minutes'].mean()
    
    # Find underperforming players (below median value)
    median_value = team_df['value'].median()
    underperforming = team_df[team_df['value'] < median_value].sort_values('value')
    
    # Find potential replacements for each underperforming player
    replacements = {}
    for _, player in underperforming.iterrows():
        position = player['position']
        budget = (player['now_cost'] + 5) / 10  # Allow for 0.5 more
        
        better_options = get_player_recommendations(
            all_players, 
            position=position, 
            budget=budget, 
            count=3
        )
        
        # Only recommend players not already in the team
        better_options = better_options[~better_options['id'].isin(team_ids)]
        
        if not better_options.empty:
            replacements[player['web_name']] = better_options['web_name'].tolist()
    
    return {
        "metrics": {
            "total_value": total_value,
            "total_points": total_points,
            "avg_minutes": avg_minutes
        },
        "underperforming": underperforming['web_name'].tolist(),
        "replacements": replacements
    }

def get_upcoming_fixtures(team_id, fixtures_data, events_data, num_fixtures=5):
    """Get upcoming fixtures for a team."""
    current_gw = get_current_gameweek(events_data)
    
    upcoming = []
    for fixture in fixtures_data:
        if fixture['event'] and fixture['event'] >= current_gw:
            if fixture['team_h'] == team_id:
                opponent_id = fixture['team_a']
                is_home = True
            elif fixture['team_a'] == team_id:
                opponent_id = fixture['team_h']
                is_home = False
            else:
                continue
                
            # Get team name for the opponent
            for team in events_data:
                if team['id'] == opponent_id:
                    opponent_name = team['name']
                    break
            else:
                opponent_name = f"Team {opponent_id}"
                
            fixture_info = {
                "gameweek": fixture['event'],
                "opponent": opponent_name,
                "is_home": is_home,
                "difficulty": fixture['difficulty']
            }
            upcoming.append(fixture_info)
            
            if len(upcoming) >= num_fixtures:
                break
                
    return upcoming

# Function to process the user's message and get a response
def get_assistant_response(prompt, fpl_data=None, fixtures_data=None, user_team=None):
    """Send the user's query to the ChatGPT API with FPL context."""
    
    # Add FPL data context to the prompt
    if fpl_data:
        # Preprocess and get current gameweek
        players_df = preprocess_player_data(fpl_data)
        events = fpl_data['events']
        current_gw = get_current_gameweek(events)
        
        # Get top performers
        top_scorers = players_df.sort_values('total_points', ascending=False).head(5)
        top_value = players_df.sort_values('value', ascending=False).head(5)
        
        # Add context about the data
        context = f"""
        You are an FPL Assistant with access to the latest Fantasy Premier League data.
        
        Current Gameweek: {current_gw}
        
        Top Point Scorers:
        {top_scorers[['web_name', 'team_name', 'total_points']].to_string(index=False)}
        
        Best Value Players:
        {top_value[['web_name', 'team_name', 'value', 'now_cost']].rename(columns={'now_cost': 'cost'}).to_string(index=False)}
        """
        
        # Add user team context if available
        if user_team:
            team_analysis = analyze_user_team(user_team, players_df)
            
            context += f"""
            User's Team Analysis:
            Team Value: £{team_analysis['metrics']['total_value']}m
            Total Points: {team_analysis['metrics']['total_points']}
            
            Potential Improvements:
            """
            
            for player, replacements in team_analysis['replacements'].items():
                context += f"Consider replacing {player} with one of: {', '.join(replacements)}\n"
        
        # Combine context with the user's question
        full_prompt = context + "\n\nUser Question: " + prompt
    else:
        full_prompt = prompt
    
    try:
        # Make API call to ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Fantasy Premier League assistant."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error getting response: {str(e)}"
    