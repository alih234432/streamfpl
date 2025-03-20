import streamlit as st
import pandas as pd
import requests
import os
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
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Chatbot Prompt Template
chat_prompt = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template="""
    You are an AI assistant specialized in Fantasy Premier League (FPL).
    Answer user queries based on current fixtures, injuries, and team management.

    Chat History:
    {chat_history}

    User: {user_input}
    AI:
    """
)

# Create an AI Chain for structured interaction
chat_chain = LLMChain(llm=llm, prompt=chat_prompt, memory=memory)

# ---------------------------- HELPER FUNCTIONS ----------------------------
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

# ---------------------------- CHATBOT MODULE ----------------------------
def chat_with_gpt(user_input):
    """Processes user queries using LangChain AI Chain"""
    response = chat_chain.run(user_input=user_input)
    return response

def chatbot():
    """Handles AI chatbot interactions with memory"""
    st.title("FPL AI Chatbot")
    st.write("Ask me anything about Fantasy Premier League!")

    user_input = st.text_area("You:")
    if st.button("Send"):
        if user_input:
            response = chat_with_gpt(user_input)
            st.write("**ChatGPT:**", response)
        else:
            st.warning("Please enter a message.")

# ---------------------------- TEAM MANAGEMENT MODULE ----------------------------
def team_advice(team_id):
    """Fetch and analyze a user's team"""
    st.title("Custom Team Advice")
    team_data = fetch_fpl_data(f"entry/{team_id}/event/1/picks/")  # Fetch user’s team data
    if team_data:
        st.write("Team data fetched successfully!")
        # Process and display advice based on fetched data

# ---------------------------- FIXTURE & PLAYER ANALYSIS MODULE ----------------------------
def fixture_analysis(weeks=5):
    """Analyze fixtures for the best teams to target"""
    st.title(f"Fixture Analysis (Next {weeks} Weeks)")
    fixture_data = fetch_fpl_data("fixtures/")
    if fixture_data:
        st.write("Fixtures loaded successfully!")
        # Process and display fixture analysis here

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
        fixture_analysis()
    elif choice == "Notifications":
        notifications()

# ---------------------------- RUN THE APP ----------------------------
if __name__ == "__main__":
    if "authenticated" not in st.session_state:
        login()
    main()
