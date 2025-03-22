import streamlit as st
import pandas as pd
import json
from datetime import datetime
import time
import matplotlib.pyplot as plt
import seaborn as sns

# Import data modules
from fplcore.api_client import get_fpl_data, get_fixtures_data, get_player_data
from fplcore.players import preprocess_player_data, get_current_gameweek, get_player_recommendations, get_top_performers
from fplcore.team_analyzer import analyze_user_team
from fplcore.fixture import get_upcoming_fixtures
from fplcore.assistant import get_assistant_response

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

# Sidebar for API key and team input
with st.sidebar:
    st.title("⚽ FPL Assistant")
    
    # OpenAI API key input
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")
    
    st.divider()
    
    # User team input
    st.subheader("Your FPL Team")
    st.write("Enter your team ID or player IDs to get personalized advice")
    
    team_input_option = st.radio(
        "Input method:",
        ["Team ID", "Manual Player Selection"]
    )
    
    if team_input_option == "Team ID":
        team_id = st.text_input("Enter your FPL Team ID:")
        if team_id and st.button("Load Team"):
            st.info("Team loading functionality to be implemented")
            # This would require additional API endpoints and possibly authentication
    else:
        # Get FPL data first
        try:
            fpl_data = get_fpl_data()
            all_players = preprocess_player_data(fpl_data)
            
            # Group by position for organized selection
            positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
            
            st.write("Select your players:")
            selected_players = []
            
            for position in positions:
                position_players = all_players[all_players['position'] == position]
                options = position_players['web_name'].tolist()
                
                # Get number to select based on position
                if position == 'Goalkeeper':
                    num_to_select = st.number_input(f"Number of {position}s:", min_value=1, max_value=2, value=2)
                elif position == 'Defender':
                    num_to_select = st.number_input(f"Number of {position}s:", min_value=3, max_value=5, value=5)
                elif position == 'Midfielder':
                    num_to_select = st.number_input(f"Number of {position}s:", min_value=2, max_value=5, value=5)
                else:  # Forward
                    num_to_select = st.number_input(f"Number of {position}s:", min_value=1, max_value=3, value=3)
                
                selected = st.multiselect(
                    f"Select {position}s:", 
                    options,
                    max_selections=num_to_select
                )
                
                # Get player IDs for selected players
                for player_name in selected:
                    player_id = position_players[position_players['web_name'] == player_name]['id'].values[0]
                    selected_players.append(player_id)
            
            if st.button("Save Team"):
                if len(selected_players) == 15:  # A valid FPL team has 15 players
                    st.session_state.user_team = selected_players
                    st.success("Team saved!")
                else:
                    st.error(f"You need to select exactly 15 players (currently {len(selected_players)})")
        except Exception as e:
            st.error(f"Error loading FPL data: {str(e)}")
    
    st.divider()
    
    # Data exploration options
    st.subheader("Data Explorer")
    
    if st.button("Show Top Performers"):
        try:
            fpl_data = get_fpl_data()
            players_df = preprocess_player_data(fpl_data)
            top_players = get_top_performers(players_df, category='total_points', count=10)
            
            st.write("Top 10 Players by Points:")
            st.dataframe(
                top_players[['web_name', 'team_name', 'position', 'total_points', 'now_cost']].rename(
                    columns={'now_cost': 'cost (£)', 'web_name': 'Player', 'team_name': 'Team', 
                            'position': 'Position', 'total_points': 'Points'}
                )
            )
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    if st.button("Show Best Value Players"):
        try:
            fpl_data = get_fpl_data()
            players_df = preprocess_player_data(fpl_data)
            value_players = get_top_performers(players_df, category='value', count=10)
            
            st.write("Top 10 Players by Value (Points/Cost):")
            st.dataframe(
                value_players[['web_name', 'team_name', 'position', 'value', 'total_points', 'now_cost']].rename(
                    columns={'now_cost': 'cost (£)', 'web_name': 'Player', 'team_name': 'Team', 
                            'position': 'Position', 'total_points': 'Points', 'value': 'Value'}
                )
            )
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

# Main chat interface
st.title("Fantasy Premier League Assistant")
st.write("Ask questions about FPL stats, get team advice, and more!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask about FPL data, players, or your team..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Get FPL data
            with st.spinner("Fetching FPL data..."):
                fpl_data = get_fpl_data()
                fixtures_data = get_fixtures_data()
            
            # Get response from assistant
            with st.spinner("Getting response..."):
                if api_key:
                    try:
                        full_response = get_assistant_response(
                            prompt, 
                            fpl_data=fpl_data,
                            fixtures_data=fixtures_data,
                            user_team=st.session_state.user_team,
                            api_key=api_key
                        )
                        message_placeholder.write(full_response)
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        message_placeholder.error(error_msg)
                        # Add error message to chat history
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                else:
                    api_key_msg = "Please enter your OpenAI API key in the sidebar to enable chat functionality."
                    message_placeholder.warning(api_key_msg)
                    # Add message to chat history
                    st.session_state.messages.append({"role": "assistant", "content": api_key_msg})
        except Exception as e:
            error_msg = f"Error fetching data: {str(e)}"
            message_placeholder.error(error_msg)
            # Add error message to chat history
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    # Main application entry point
    # You could add additional initialization here if needed
    pass