import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime

from config import FPL_API_BASE, DATA_FOLDER
from fplcore.logger import log_info, log_error

def login():
    """Handles user authentication"""
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        # In a real application, validate credentials here
        st.session_state["authenticated"] = True
        st.success(f"Welcome, {username}!")
        log_info(f"User logged in: {username}")

def logout():
    """Handles user logout"""
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        log_info("User logged out")

def save_user_settings(settings):
    """Save user settings to a JSON file"""
    try:
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
            
        username = settings.get('username', 'default_user')
        filename = f"{DATA_FOLDER}user_{username}_settings.json"
        
        with open(filename, 'w') as f:
            json.dump(settings, f)
            
        log_info(f"Settings saved for user: {username}")
        return True
    except Exception as e:
        log_error(f"Error saving user settings: {e}")
        return False

def load_user_settings(username):
    """Load user settings from a JSON file"""
    try:
        filename = f"{DATA_FOLDER}user_{username}_settings.json"
        
        if not os.path.exists(filename):
            return {}
            
        with open(filename, 'r') as f:
            settings = json.load(f)
            
        log_info(f"Settings loaded for user: {username}")
        return settings
    except Exception as e:
        log_error(f"Error loading user settings: {e}")
        return {}

def save_conversation_history(username, history):
    """Save conversation history to a JSON file"""
    try:
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
            
        filename = f"{DATA_FOLDER}user_{username}_conversation.json"
        
        # Add timestamp to each message if not already present
        timestamped_history = []
        for message in history:
            if 'timestamp' not in message:
                message['timestamp'] = datetime.now().isoformat()
            timestamped_history.append(message)
        
        with open(filename, 'w') as f:
            json.dump(timestamped_history, f)
            
        log_info(f"Conversation history saved for user: {username}")
        return True
    except Exception as e:
        log_error(f"Error saving conversation history: {e}")
        return False

def load_conversation_history(username):
    """Load conversation history from a JSON file"""
    try:
        filename = f"{DATA_FOLDER}user_{username}_conversation.json"
        
        if not os.path.exists(filename):
            return []
            
        with open(filename, 'r') as f:
            history = json.load(f)
            
        log_info(f"Conversation history loaded for user: {username}")
        return history
    except Exception as e:
        log_error(f"Error loading conversation history: {e}")
        return []

def settings_page():
    """User settings page"""
    st.title("User Settings")
    
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.warning("Please log in to access settings.")
        return
    
    # Get current username
    username = st.session_state.get("username", "default_user")
    
    # Load current settings
    current_settings = load_user_settings(username)
    
    # User profile settings
    st.subheader("Profile Settings")
    display_name = st.text_input("Display Name", value=current_settings.get("display_name", username))
    email = st.text_input("Email", value=current_settings.get("email", ""))
    
    # FPL Team settings
    st.subheader("FPL Team Settings")
    fpl_id = st.text_input("FPL Team ID", value=current_settings.get("fpl_id", ""))
    
    # Notification preferences
    st.subheader("Notification Preferences")
    notify_injuries = st.checkbox("Injury Updates", value=current_settings.get("notify_injuries", True))
    notify_price_changes = st.checkbox("Price Changes", value=current_settings.get("notify_price_changes", True))
    notify_deadlines = st.checkbox("Upcoming Deadlines", value=current_settings.get("notify_deadlines", True))
    
    # Theme preferences
    st.subheader("Theme Preferences")
    theme_options = ["Light", "Dark", "System Default"]
    theme = st.selectbox("Theme", theme_options, index=theme_options.index(current_settings.get("theme", "System Default")))
    
    # Save settings
    if st.button("Save Settings"):
        # Compile settings
        settings = {
            "username": username,
            "display_name": display_name,
            "email": email,
            "fpl_id": fpl_id,
            "notify_injuries": notify_injuries,
            "notify_price_changes": notify_price_changes,
            "notify_deadlines": notify_deadlines,
            "theme": theme,
            "last_updated": datetime.now().isoformat()
        }
        
        # Save to file
        if save_user_settings(settings):
            st.success("Settings saved successfully!")
            # Update session state
            st.session_state["username"] = username
            st.session_state["fpl_id"] = fpl_id
        else:
            st.error("Failed to save settings. Please try again.")