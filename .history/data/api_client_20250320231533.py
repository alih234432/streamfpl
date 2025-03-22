import requests
import streamlit as st
import pandas as pd

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

def get_team_data(team_id):
    """This would fetch a user's team data (to be implemented)"""
    # This would require authentication with FPL API
    # For now, just a placeholder
    pass