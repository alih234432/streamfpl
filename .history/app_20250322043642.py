import streamlit as st
import os
from fplcore.chatbot import chatbot
from fplcore.fixture import fixture_analysis
from fplcore.fpl_rules import rules_reference
from fplcore.players import team_advice
from fplcore.user import login
from fplcore.notifications import notifications
from config import DATA_FOLDER
from fplcore.logger import log_info

def ensure_data_folder():
    """Ensure the data directory exists"""
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        log_info(f"Created data directory: {DATA_FOLDER}")
    
    # No call to check_required_files() to avoid the error

def main():
    """Main application entry point with navigation"""
    st.sidebar.title("Navigation")
    options = ["Home", "Chatbot", "Team Advice", "Fixtures", "Rules Reference", "Notifications"]
    choice = st.sidebar.radio("Go to", options)

    if choice == "Home":
        st.title("Welcome to the FPL Chatbot!")
        st.write("Use the sidebar to navigate through different sections of the app.")
        st.write("The chatbot is powered by AI and has expert knowledge of FPL rules, fixtures, and strategy.")
        
        # Display key features
        st.subheader("Key Features:")
        st.markdown("- **AI Chatbot:** Get answers to any FPL question")
        st.markdown("- **Team Advice:** Personalized suggestions for your FPL team")
        st.markdown("- **Fixture Analysis:** Upcoming matches and difficulty ratings")
        st.markdown("- **Rules Reference:** Complete FPL rules and terminology")
        st.markdown("- **Notifications:** Latest injury updates and price changes")
        
    elif choice == "Chatbot":
        chatbot()
    elif choice == "Team Advice":
        team_id = st.text_input("Enter your FPL Team ID:")
        if st.button("Get Advice"):
            team_advice(team_id)
    elif choice == "Fixtures":
        weeks = st.slider("Number of weeks to analyze:", 1, 10, 5)
        fixture_analysis(weeks)
    elif choice == "Rules Reference":
        rules_reference()
    elif choice == "Notifications":
        notifications()

# Run the app
if __name__ == "__main__":
    # Ensure data directory exists
    ensure_data_folder()
    
    if "authenticated" not in st.session_state:
        login()
    main()  # Always call main() to show navigation