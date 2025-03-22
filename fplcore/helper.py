import streamlit as st
import requests
import json
import os
import pandas as pd
from datetime import datetime

from config import FPL_API_BASE, DATA_FOLDER
from fplcore.logger import log_error, log_info

def fetch_fpl_data(endpoint):
    """Generic function to fetch data from FPL API"""
    try:
        response = requests.get(f"{FPL_API_BASE}{endpoint}")
        return response.json()
    except Exception as e:
        log_error(f"Error fetching data from {endpoint}: {e}")
        return None

def save_data_to_file(data, filename):
    """Save data to a file in the data folder"""
    try:
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
            
        filepath = os.path.join(DATA_FOLDER, filename)
        
        # Handle different data types
        if isinstance(data, pd.DataFrame):
            # Save DataFrame to CSV
            data.to_csv(filepath, index=False)
        else:
            # Save dictionary/list to JSON
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
        log_info(f"Data saved to {filepath}")
        return True
    except Exception as e:
        log_error(f"Error saving data to {filename}: {e}")
        return False

def load_data_from_file(filename, file_type=None):
    """Load data from a file in the data folder"""
    try:
        filepath = os.path.join(DATA_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return None
        
        # Determine file type if not specified
        if file_type is None:
            if filename.endswith('.csv'):
                file_type = 'csv'
            elif filename.endswith('.json'):
                file_type = 'json'
            else:
                file_type = 'txt'
        
        # Load based on file type
        if file_type == 'csv':
            data = pd.read_csv(filepath)
        elif file_type == 'json':
            with open(filepath, 'r') as f:
                data = json.load(f)
        else:
            with open(filepath, 'r') as f:
                data = f.read()
        
        log_info(f"Data loaded from {filepath}")
        return data
    except Exception as e:
        log_error(f"Error loading data from {filename}: {e}")
        return None

def format_timestamp(timestamp_str):
    """Convert API timestamp to readable format"""
    try:
        dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%d %b %Y - %H:%M')
    except Exception as e:
        log_error(f"Error formatting timestamp {timestamp_str}: {e}")
        return timestamp_str

def calculate_player_value(player_data):
    """Calculate player value (points per million)"""
    try:
        points = float(player_data['total_points'])
        cost = float(player_data['now_cost']) / 10.0  # Convert to millions
        if cost > 0:
            value = points / cost
            return round(value, 1)
        return 0
    except Exception as e:
        log_error(f"Error calculating player value: {e}")
        return 0

def format_currency(value):
    """Format a number as currency (£)"""
    return f"£{value:.1f}m"

def get_difficulty_color(difficulty):
    """Get color based on fixture difficulty rating (FDR)"""
    colors = {
        1: '#00ff00',  # Very easy - bright green
        2: '#92d050',  # Easy - light green
        3: '#ffff00',  # Medium - yellow
        4: '#ff9900',  # Difficult - orange
        5: '#ff0000'   # Very difficult - red
    }
    return colors.get(difficulty, '#ffffff')  # Default white

def create_progress_bar(value, max_value=100, color="#4CAF50"):
    """Create a simple HTML progress bar"""
    percent = min(100, int((value / max_value) * 100))
    return f"""
    <div style="width:100%; background-color:#f0f0f0; border-radius:3px;">
        <div style="width:{percent}%; background-color:{color}; height:20px; border-radius:3px;">
            <div style="text-align:center; color:white; padding:3px;">{value}</div>
        </div>
    </div>
    """

def display_fancy_metric(label, value, delta=None, delta_color="normal"):
    """Display a metric with a fancy style"""
    if delta is not None:
        st.metric(label=label, value=value, delta=delta, delta_color=delta_color)
    else:
        st.metric(label=label, value=value)

def get_position_abbreviation(position_id):
    """Convert position ID to abbreviation"""
    positions = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
    return positions.get(position_id, "UNK")

def get_status_emoji(status):
    """Get emoji for player status"""
    status_map = {
        'a': '✅',  # Available
        'd': '⚠️',  # Doubtful
        'i': '🚑',  # Injured
        'n': '❌',  # Not Available
        's': '🟨'   # Suspended
    }
    return status_map.get(status, '❓')