import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from config import FPL_API_BASE
from fplcore.logger import log_error

def get_teams_data():
    """Fetch team data from FPL API and create a mapping of team IDs to names"""
    try:
        response = requests.get(f"{FPL_API_BASE}bootstrap-static/")
        data = response.json()
        teams = {team['id']: team['name'] for team in data['teams']}
        return teams
    except Exception as e:
        log_error(f"Error fetching team data: {e}")
        st.error(f"Error fetching team data: {e}")
        return {}

def get_fixtures_data():
    """Fetch all fixtures data from FPL API"""
    try:
        response = requests.get(f"{FPL_API_BASE}fixtures/")
        fixtures = response.json()
        return fixtures
    except Exception as e:
        log_error(f"Error fetching fixtures data: {e}")
        st.error(f"Error fetching fixtures data: {e}")
        return []

def format_fixtures(fixtures, teams):
    """Format fixtures data for better readability"""
    formatted_fixtures = []
    
    for fixture in fixtures:
        # Convert timestamp to datetime
        if fixture['kickoff_time']:
            kickoff_time = datetime.strptime(fixture['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ')
            kickoff_str = kickoff_time.strftime('%d %b %Y - %H:%M')
        else:
            kickoff_str = "TBD"
        
        home_team = teams.get(fixture['team_h'], 'Unknown')
        away_team = teams.get(fixture['team_a'], 'Unknown')
        
        game_week = fixture['event']
        
        # Format the score if the match has been played
        if fixture['finished']:
            score = f"{fixture['team_h_score']} - {fixture['team_a_score']}"
        else:
            score = "vs"
        
        formatted_fixture = {
            'gameweek': game_week,
            'home_team': home_team,
            'away_team': away_team,
            'kickoff_time': kickoff_str,
            'score': score,
            'finished': fixture['finished']
        }
        
        formatted_fixtures.append(formatted_fixture)
    
    return formatted_fixtures

def get_current_gameweek():
    """Get the current gameweek from FPL API"""
    try:
        response = requests.get(f"{FPL_API_BASE}bootstrap-static/")
        data = response.json()
        for event in data['events']:
            if event['is_current']:
                return event['id']
        return None
    except Exception as e:
        log_error(f"Error fetching current gameweek: {e}")
        st.error(f"Error fetching current gameweek: {e}")
        return None

def get_fixtures_for_gameweek(gameweek):
    """Get fixtures for a specific gameweek"""
    teams = get_teams_data()
    fixtures = get_fixtures_data()
    
    if not teams or not fixtures:
        return []
    
    gameweek_fixtures = [fixture for fixture in fixtures if fixture['event'] == gameweek]
    return format_fixtures(gameweek_fixtures, teams)

def get_team_fixtures(team_name, num_fixtures=5):
    """Get upcoming fixtures for a specific team"""
    teams = get_teams_data()
    fixtures = get_fixtures_data()
    
    if not teams or not fixtures:
        return []
    
    # Find team ID from name
    team_id = None
    for id, name in teams.items():
        if name.lower() == team_name.lower():
            team_id = id
            break
    
    if not team_id:
        return []
    
    # Get fixtures where the team is playing (either home or away)
    team_fixtures = [fixture for fixture in fixtures 
                     if (fixture['team_h'] == team_id or fixture['team_a'] == team_id) 
                     and not fixture['finished']]
    
    # Sort by event/gameweek
    team_fixtures.sort(key=lambda x: x['event'])
    
    # Limit to specified number of fixtures
    team_fixtures = team_fixtures[:num_fixtures]
    
    return format_fixtures(team_fixtures, teams)

def get_fixtures_summary():
    """Get a summary of fixtures for the current and next gameweek"""
    current_gw = get_current_gameweek()
    if not current_gw:
        return "Could not determine current gameweek."
    
    current_fixtures = get_fixtures_for_gameweek(current_gw)
    next_fixtures = get_fixtures_for_gameweek(current_gw + 1)
    
    summary = f"Current Gameweek ({current_gw}) Fixtures:\n"
    for fixture in current_fixtures:
        summary += f"- {fixture['home_team']} {fixture['score']} {fixture['away_team']} ({fixture['kickoff_time']})\n"
    
    summary += f"\nNext Gameweek ({current_gw + 1}) Fixtures:\n"
    for fixture in next_fixtures:
        summary += f"- {fixture['home_team']} vs {fixture['away_team']} ({fixture['kickoff_time']})\n"
    
    return summary

def fixture_analysis(weeks=5):
    """Analyze upcoming fixtures for difficulty and double gameweeks"""
    st.title("Fixture Analysis")
    
    # Get current gameweek
    current_gw = get_current_gameweek()
    if not current_gw:
        st.error("Could not determine current gameweek.")
        return
    
    # Get fixtures for the specified number of gameweeks
    all_fixtures = []
    for gw in range(current_gw, current_gw + weeks):
        gw_fixtures = get_fixtures_for_gameweek(gw)
        all_fixtures.extend(gw_fixtures)
    
    # Analyze for double gameweeks
    gw_team_count = {}
    for fixture in all_fixtures:
        gw = fixture['gameweek']
        home_team = fixture['home_team']
        away_team = fixture['away_team']
        
        if gw not in gw_team_count:
            gw_team_count[gw] = {}
        
        if home_team not in gw_team_count[gw]:
            gw_team_count[gw][home_team] = 0
        if away_team not in gw_team_count[gw]:
            gw_team_count[gw][away_team] = 0
        
        gw_team_count[gw][home_team] += 1
        gw_team_count[gw][away_team] += 1
    
    # Display double gameweeks if any
    dgw_found = False
    for gw, teams in gw_team_count.items():
        double_gw_teams = [team for team, count in teams.items() if count > 1]
        if double_gw_teams:
            if not dgw_found:
                st.subheader("Double Gameweeks")
                dgw_found = True
            st.write(f"Gameweek {gw}: {', '.join(double_gw_teams)}")
    
    if not dgw_found:
        st.info("No double gameweeks found in the analyzed period.")
    
    # Display the full fixture table
    st.subheader("Upcoming Fixtures")
    
    # Convert to DataFrame for easier display
    fixture_data = []
    for fixture in all_fixtures:
        fixture_data.append({
            'Gameweek': fixture['gameweek'],
            'Home Team': fixture['home_team'],
            'Away Team': fixture['away_team'],
            'Date & Time': fixture['kickoff_time']
        })
    
    fixture_df = pd.DataFrame(fixture_data)
    st.dataframe(fixture_df)

def extract_team_name(query):
    """Extract team name from user query if they're asking about specific team fixtures"""
    query = query.lower()
    if "fixture" in query or "fixtures" in query or "playing" in query or "games" in query:
        # Get all team names from API
        teams = get_teams_data()
        team_names = [name.lower() for name in teams.values()]
        
        # Check if any team name is in the query
        for team_name in team_names:
            if team_name.lower() in query:
                return team_name
    return None