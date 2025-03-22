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
                data = json