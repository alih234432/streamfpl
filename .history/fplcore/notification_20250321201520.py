import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

from config import FPL_API_BASE, DATA_FOLDER
from fplcore.logger import log_error, log_info

def get_player_status_changes():
    """Get players with recent status changes (injuries, returns, etc.)"""
    try:
        # Get current player data
        response = requests.get(f"{FPL_API_BASE}bootstrap-static/")
        data = response.json()
        players = data['elements']
        
        # Filter players with status changes
        status_players = [p for p in players if p['status'] != 'a']  # 'a' means available
        
        # Add more info to each player
        for player in status_players:
            # Get team name
            team_id = player['team']
            team_name = next((t['name'] for t in data['teams'] if t['id'] == team_id), "Unknown")
            player['team_name'] = team_name
            
            # Get position name
            element_type = player['element_type']
            position = next((t['singular_name_short'] for t in data['element_types'] if t['id'] == element_type), "Unknown")
            player['position'] = position
            
            # Format status
            status_map = {
                'd': 'Doubtful',
                'i': 'Injured',
                'n': 'Not Available',
                's': 'Suspended'
            }
            player['status_desc'] = status_map.get(player['status'], player['status'])
            
            # Format price
            player['price'] = player['now_cost'] / 10.0
        
        return status_players
    except Exception as e:
        log_error(f"Error fetching player status changes: {e}")
        return []

def get_price_changes():
    """Get players with recent price changes"""
    try:
        # Get current player data
        response = requests.get(f"{FPL_API_BASE}bootstrap-static/")
        data = response.json()
        players = data['elements']
        
        # Filter players with price changes
        price_change_players = [p for p in players if p['cost_change_event'] != 0]
        
        # Add more info to each player
        for player in price_change_players:
            # Get team name
            team_id = player['team']
            team_name = next((t['name'] for t in data['teams'] if t['id'] == team_id), "Unknown")
            player['team_name'] = team_name
            
            # Get position name
            element_type = player['element_type']
            position = next((t['singular_name_short'] for t in data['element_types'] if t['id'] == element_type), "Unknown")
            player['position'] = position
            
            # Format price info
            player['old_price'] = (player['now_cost'] - player['cost_change_event']) / 10.0
            player['new_price'] = player['now_cost'] / 10.0
            player['price_change'] = player['cost_change_event'] / 10.0
        
        return price_change_players
    except Exception as e:
        log_error(f"Error fetching price changes: {e}")
        return []

def get_upcoming_deadlines():
    """Get upcoming gameweek deadlines"""
    try:
        # Get gameweek data
        response = requests.get(f"{FPL_API_BASE}bootstrap-static/")
        data = response.json()
        gameweeks = data['events']
        
        # Filter future gameweeks
        current_time = datetime.now()
        future_gameweeks = []
        
        for gw in gameweeks:
            deadline_time = datetime.strptime(gw['deadline_time'], '%Y-%m-%dT%H:%M:%SZ')
            if deadline_time > current_time:
                # Calculate time remaining
                time_remaining = deadline_time - current_time
                days = time_remaining.days
                hours = time_remaining.seconds // 3600
                minutes = (time_remaining.seconds % 3600) // 60
                
                gw['deadline_formatted'] = deadline_time.strftime('%d %b %Y - %H:%M')
                gw['time_remaining'] = f"{days}d {hours}h {minutes}m"
                future_gameweeks.append(gw)
        
        # Sort by deadline
        future_gameweeks.sort(key=lambda x: datetime.strptime(x['deadline_time'], '%Y-%m-%dT%H:%M:%SZ'))
        
        return future_gameweeks[:3]  # Return the next 3 deadlines
    except Exception as e:
        log_error(f"Error fetching upcoming deadlines: {e}")
        return []

def notifications():
    """Display notifications and alerts page"""
    st.title("Notifications & Alerts")
    
    # Create tabs for different notification types
    tab1, tab2, tab3 = st.tabs(["Injury Updates", "Price Changes", "Deadlines"])
    
    with tab1:
        st.header("Recent Injury & Status Updates")
        status_changes = get_player_status_changes()
        
        if status_changes:
            # Convert to DataFrame for easier display
            df = pd.DataFrame(status_changes)
            df = df[['web_name', 'team_name', 'position', 'status_desc', 'news', 'price', 'selected_by_percent']]
            df.columns = ['Player', 'Team', 'Pos', 'Status', 'News', 'Price (£M)', 'Selected By (%)']
            
            # Show the data
            st.dataframe(df, use_container_width=True)
            
            # Filter by teams
            teams = sorted(df['Team'].unique())
            selected_team = st.selectbox("Filter by team:", ["All Teams"] + list(teams))
            
            if selected_team != "All Teams":
                filtered_df = df[df['Team'] == selected_team]
                st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("No recent status changes found.")
    
    with tab2:
        st.header("Recent Price Changes")
        price_changes = get_price_changes()
        
        if price_changes:
            # Convert to DataFrame for easier display
            df = pd.DataFrame(price_changes)
            df = df[['web_name', 'team_name', 'position', 'old_price', 'new_price', 'price_change', 'selected_by_percent']]
            df.columns = ['Player', 'Team', 'Pos', 'Old Price (£M)', 'New Price (£M)', 'Change (£M)', 'Selected By (%)']
            
            # Show risers and fallers separately
            st.subheader("Price Risers")
            risers = df[df['Change (£M)'] > 0].sort_values(by='Change (£M)', ascending=False)
            if not risers.empty:
                st.dataframe(risers, use_container_width=True)
            else:
                st.info("No price risers found.")
            
            st.subheader("Price Fallers")
            fallers = df[df['Change (£M)'] < 0].sort_values(by='Change (£M)')
            if not fallers.empty:
                st.dataframe(fallers, use_container_width=True)
            else:
                st.info("No price fallers found.")
        else:
            st.info("No recent price changes found.")
    
    with tab3:
        st.header("Upcoming Deadlines")
        deadlines = get_upcoming_deadlines()
        
        if deadlines:
            # Show deadlines with countdown
            for i, gw in enumerate(deadlines):
                if i == 0:
                    st.subheader(f"Next Deadline: GW{gw['id']} - {gw['deadline_formatted']}")
                    st.info(f"Time Remaining: {gw['time_remaining']}")
                else:
                    st.write(f"GW{gw['id']} - {gw['deadline_formatted']} (in {gw['time_remaining']})")
            
            # Add a reminder button
            if st.button("Set Reminder"):
                st.success(f"Reminder set for GW{deadlines[0]['id']} deadline!")
                log_info(f"User set reminder for GW{deadlines[0]['id']}")
        else:
            st.info("No upcoming deadlines found.")