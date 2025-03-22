import streamlit as st
import pandas as pd
import requests
import os
import json
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# ---------------------------- CONFIG & GLOBAL VARIABLES ----------------------------
DATA_FOLDER = "data/"  # Path to your stored data
FPL_API_BASE = "https://fantasy.premierleague.com/api/"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI LLM with LangChain
llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)

# Conversation Memory (Keeps chat context)
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    input_key="user_input",
    return_messages=True
)


# ---------------------------- FIXTURE DATA MANAGEMENT ----------------------------
def get_teams_data():
    """Fetch team data from FPL API and create a mapping of team IDs to names"""
    try:
        response = requests.get(f"{FPL_API_BASE}bootstrap-static/")
        data = response.json()
        teams = {team['id']: team['name'] for team in data['teams']}
        return teams
    except Exception as e:
        st.error(f"Error fetching team data: {e}")
        return {}

def get_fixtures_data():
    """Fetch all fixtures data from FPL API"""
    try:
        response = requests.get(f"{FPL_API_BASE}fixtures/")
        fixtures = response.json()
        return fixtures
    except Exception as e:
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

# ---------------------------- CHATBOT MODULE WITH FIXTURES INTEGRATION ----------------------------
# Enhanced prompt template with fixture knowledge
chat_prompt = PromptTemplate(
    input_variables=["chat_history", "user_input", "fixtures_data"],
    template="""
    You are an AI assistant specialized in Fantasy Premier League (FPL).
    Answer user queries based on current fixtures, injuries, and team management.
    
    Here is the latest fixture information:
    {fixtures_data}
    
    Chat History:
    {chat_history}
    
    User: {user_input}
    AI:
    """
)

# Create an AI Chain for structured interaction
chat_chain = LLMChain(llm=llm, prompt=chat_prompt, memory=memory)

def chat_with_gpt(user_input):
    """Processes user queries using LangChain AI Chain with fixtures data"""
    # Get fixtures summary for the current and next gameweek
    fixtures_data = get_fixtures_summary()
    
    # Check if the query is about a specific team's fixtures
    team_name = extract_team_name(user_input)
    if team_name:
        team_fixtures = get_team_fixtures(team_name)
        if team_fixtures:
            team_fixtures_str = f"Upcoming fixtures for {team_name}:\n"
            for fixture in team_fixtures:
                opponent = fixture['away_team'] if fixture['home_team'] == team_name else fixture['home_team']
                home_or_away = "Home" if fixture['home_team'] == team_name else "Away"
                team_fixtures_str += f"- GW{fixture['gameweek']}: {home_or_away} vs {opponent} ({fixture['kickoff_time']})\n"
            fixtures_data += "\n\n" + team_fixtures_str
    
    response = chat_chain.run(user_input=user_input, fixtures_data=fixtures_data)
    return response

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

def chatbot():
    """Handles AI chatbot interactions with memory and fixtures data"""
    st.title("FPL AI Chatbot")
    st.write("Ask me anything about Fantasy Premier League including fixtures!")

    # Initialize conversation history in session state if it doesn't exist
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    # Display conversation history
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            st.write(f"**You:** {message['content']}")
        else:
            st.write(f"**ChatGPT:** {message['content']}")
    
    # Define a callback for form submission
    def process_input():
        if st.session_state.user_input:
            # Get user input from session state
            user_input = st.session_state.user_input
            
            # Add user message to conversation history
            st.session_state.conversation_history.append({"role": "user", "content": user_input})
            
            # Get response from AI
            response = chat_with_gpt(user_input)
            
            # Add AI response to conversation history
            st.session_state.conversation_history.append({"role": "assistant", "content": response})
            
            # Clear the input field
            st.session_state.user_input = ""
    
    # Create a form that will submit when Enter is pressed
    with st.form(key="chat_form", clear_on_submit=False):
        # Text input for user message
        st.text_input("You:", key="user_input")
        
        # Submit button (hidden or visible)
        submitted = st.form_submit_button("Send", on_click=process_input)
        
        # Instructions
        st.caption("Press Enter to send your message")


def fetch_fpl_data(endpoint):
    """Fetch data from the official FPL API"""
    try:
        response = requests.get(FPL_API_BASE + endpoint)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def load_local_data(filename):
    """Load stored data from the data folder"""
    try:
        return pd.read_csv(f"{DATA_FOLDER}{filename}")
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return None

# ---------------------------- AUTHENTICATION MODULE ----------------------------
def login():
    """Handles user authentication"""
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        st.session_state["authenticated"] = True
        st.success(f"Welcome, {username}!")

# ---------------------------- TEAM MANAGEMENT MODULE ----------------------------
def team_advice(team_id):
    """Fetch and analyze a user's team"""
    st.title("Custom Team Advice")
    team_data = fetch_fpl_data(f"entry/{team_id}/event/1/picks/")  # Fetch user's team data
    if team_data:
        st.write("Team data fetched successfully!")
        # Process and display advice based on fetched data

# ---------------------------- NOTIFICATIONS & ALERTS ----------------------------
def notifications():
    """Handle injury updates and price changes"""
    st.title("Notifications & Alerts")
    injury_data = fetch_fpl_data("bootstrap-static/")  # General FPL data includes injuries
    if injury_data:
        st.write("Latest Injury Updates:")
        # Process and display relevant notifications

# ---------------------------- MAIN APP NAVIGATION ----------------------------
def main():
    st.sidebar.title("Navigation")
    options = ["Home", "Chatbot", "Team Advice", "Fixtures", "Notifications"]
    choice = st.sidebar.radio("Go to", options)

    if choice == "Home":
        st.title("Welcome to the FPL Chatbot!")
        st.write("Use the sidebar to navigate.")
    elif choice == "Chatbot":
        chatbot()
    elif choice == "Team Advice":
        team_id = st.text_input("Enter your FPL Team ID:")
        if st.button("Get Advice"):
            team_advice(team_id)
    elif choice == "Fixtures":
        weeks = st.slider("Number of weeks to analyze:", 1, 10, 5)
        fixture_analysis(weeks)
    elif choice == "Notifications":
        notifications()

# ---------------------------- RUN THE APP ----------------------------
if __name__ == "__main__":
    if "authenticated" not in st.session_state:
        login()
    main()