import streamlit as st
import requests

from config import FPL_API_BASE
from fplcore.logger import log_error

def fetch_player_data():
    """Fetch all player data from FPL API"""
    try:
        response = requests.get(f"{FPL_API_BASE}bootstrap-static/")
        data = response.json()
        return data['elements']  # 'elements' contains player data
    except Exception as e:
        log_error(f"Error fetching player data: {e}")
        st.error(f"Error fetching player data: {e}")
        return []

def fetch_player_history(player_id):
    """Fetch a player's match history"""
    try:
        response = requests.get(f"{FPL_API_BASE}element-summary/{player_id}/")
        data = response.json()
        return data
    except Exception as e:
        log_error(f"Error fetching player history: {e}")
        st.error(f"Error fetching player history: {e}")
        return {}

def get_player_by_name(name):
    """Find player by name"""
    players = fetch_player_data()
    name_lower = name.lower()
    
    # Try to find exact match first
    for player in players:
        if player['web_name'].lower() == name_lower or player['first_name'].lower() + ' ' + player['second_name'].lower() == name_lower:
            return player
    
    # Try partial match
    for player in players:
        if name_lower in player['web_name'].lower() or name_lower in (player['first_name'].lower() + ' ' + player['second_name'].lower()):
            return player
    
    return None

def get_player_position(player):
    """Convert position ID to readable position"""
    positions = {1: "Goalkeeper", 2: "Defender", 3: "Midfielder", 4: "Forward"}
    return positions.get(player['element_type'], "Unknown")

def get_top_players(position=None, limit=10, sort_by='total_points'):
    """Get top players by position and sorting criteria"""
    players = fetch_player_data()
    
    # Filter by position if specified
    if position:
        position_map = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}
        position_id = position_map.get(position.upper())
        if position_id:
            players = [p for p in players if p['element_type'] == position_id]
    
    # Sort players
    players.sort(key=lambda x: x[sort_by], reverse=True)
    
    # Return top N players
    return players[:limit]

def fetch_team_info(team_id):
    """Fetch FPL team information"""
    try:
        response = requests.get(f"{FPL_API_BASE}entry/{team_id}/")
        data = response.json()
        return data
    except Exception as e:
        log_error(f"Error fetching team info: {e}")
        st.error(f"Error fetching team info: {e}")
        return None

def fetch_team_picks(team_id, gameweek):
    """Fetch team picks for a specific gameweek"""
    try:
        response = requests.get(f"{FPL_API_BASE}entry/{team_id}/event/{gameweek}/picks/")
        data = response.json()
        return data
    except Exception as e:
        log_error(f"Error fetching team picks: {e}")
        st.error(f"Error fetching team picks: {e}")
        return None

def team_advice(team_id):
    """Analyze a user's FPL team and provide advice"""
    st.title("Team Analysis")
    
    if not team_id:
        st.warning("Please enter your FPL Team ID to get personalized advice.")
        return
    
    # Fetch team information
    team_info = fetch_team_info(team_id)
    if not team_info:
        st.error("Failed to fetch team information. Please check the Team ID and try again.")
        return
    
    # Display team overview
    st.subheader(f"Team Overview: {team_info['name']}")
    st.write(f"Manager: {team_info['player_first_name']} {team_info['player_last_name']}")
    st.write(f"Overall Points: {team_info['summary_overall_points']}")
    st.write(f"Overall Rank: {team_info['summary_overall_rank']:,}")
    
    # Get current gameweek
    from fplcore.fixture import get_current_gameweek
    current_gw = get_current_gameweek()
    if not current_gw:
        st.error("Could not determine current gameweek.")
        return
    
    # Fetch team picks for current gameweek
    team_picks = fetch_team_picks(team_id, current_gw)
    if not team_picks:
        st.error(f"Failed to fetch team picks for gameweek {current_gw}.")
        return
    
    # Get all player data
    all_players = {p['id']: p for p in fetch_player_data()}
    
    # Display current team
    st.subheader(f"Current Team (Gameweek {current_gw})")
    
    # Separate players into starters and bench
    starters = [pick for pick in team_picks['picks'] if pick['position'] <= 11]
    bench = [pick for pick in team_picks['picks'] if pick['position'] > 11]
    
    # Display starters
    st.write("**Starting XI:**")
    for player in starters:
        player_data = all_players.get(player['element'])
        if player_data:
            captain_indicator = " (C)" if player['is_captain'] else " (VC)" if player['is_vice_captain'] else ""
            position = get_player_position(player_data)
            st.write(f"- {player_data['web_name']}{captain_indicator} ({position}) - {player_data['total_points']} pts")
    
    # Display bench
    st.write("**Bench:**")
    for player in bench:
        player_data = all_players.get(player['element'])
        if player_data:
            position = get_player_position(player_data)
            st.write(f"- {player_data['web_name']} ({position}) - {player_data['total_points']} pts")
    
    # Basic transfer advice based on form, fixtures, and injuries
    st.subheader("Transfer Suggestions")
    
    # Identify potential issues (injuries, suspensions, poor form)
    issues = []
    for player in team_picks['picks']:
        player_data = all_players.get(player['element'])
        if player_data:
            if player_data['status'] != 'a':  # 'a' means available
                status_map = {'d': 'doubtful', 'i': 'injured', 'n': 'not available', 's': 'suspended'}
                issues.append(f"{player_data['web_name']} is {status_map.get(player_data['status'], 'unavailable')}.")
            elif player_data['form'] and float(player_data['form']) < 2.0:
                issues.append(f"{player_data['web_name']} is in poor form ({player_data['form']}).")
    
    if issues:
        st.write("**Potential Issues:**")
        for issue in issues:
            st.write(f"- {issue}")
        
        # Simple replacement suggestions
        st.write("**Potential Replacements:**")
        for issue_player in [p['element'] for p in team_picks['picks'] if all_players.get(p['element']) and all_players.get(p['element'])['status'] != 'a']:
            player_data = all_players.get(issue_player)
            if player_data:
                position_id = player_data['element_type']
                price = player_data['now_cost'] / 10  # Convert to millions
                
                # Find similar priced players in same position with better form
                replacements = [p for p in all_players.values() 
                               if p['element_type'] == position_id 
                               and p['status'] == 'a'  # Available
                               and p['now_cost'] <= player_data['now_cost'] + 5  # Similar or slightly higher price
                               and p['id'] not in [pick['element'] for pick in team_picks['picks']]  # Not already in team
                               and float(p['form']) > 3.0]  # Good form
                
                # Sort by form
                replacements.sort(key=lambda x: float(x['form']), reverse=True)
                
                if replacements:
                    st.write(f"To replace {player_data['web_name']} ({price}m):")
                    for i, replacement in enumerate(replacements[:3]):
                        rep_price = replacement['now_cost'] / 10
                        st.write(f"  {i+1}. {replacement['web_name']} ({rep_price}m) - Form: {replacement['form']}")
    else:
        st.write("Your team looks good! No immediate issues detected.")
    
    # Fixture analysis for current players
    st.subheader("Upcoming Fixtures Analysis")
    
    # Get team data
    from fplcore.fixture import get_teams_data
    teams = get_teams_data()
    
    # Analyze fixture difficulty for each player
    for player in team_picks['picks']:
        player_data = all_players.get(player['element'])
        if player_data:
            team_id = player_data['team']
            team_name = teams.get(team_id, "Unknown")
            
            # Get team fixtures
            from fplcore.fixture import get_team_fixtures
            fixtures = get_team_fixtures(team_name, num_fixtures=3)
            
            if fixtures:
                st.write(f"**{player_data['web_name']} ({team_name}):**")
                for fixture in fixtures:
                    opponent = fixture['away_team'] if fixture['home_team'] == team_name else fixture['home_team']
                    home_or_away = "Home" if fixture['home_team'] == team_name else "Away"
                    st.write(f"- GW{fixture['gameweek']}: {home_or_away} vs {opponent}")
            else:
                st.write(f"**{player_data['web_name']} ({team_name}):** Fixture data not available.")