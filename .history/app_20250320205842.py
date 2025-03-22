import streamlit as st
import requests
import openai
import json
#test
# Set OpenAI API key manually
openai.api_key = "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"

# -----------------------------------
# 1. Fetch FPL Global Data
# -----------------------------------
@st.cache_data
def get_fpl_data():
    """
    Retrieve comprehensive Fantasy Premier League data.
    """
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    data = response.json()
    return data

fpl_data = get_fpl_data()
players = fpl_data.get("elements", [])
teams = fpl_data.get("teams", [])

# -----------------------------------
# 2. Fetch a Specific FPL Team by ID
# -----------------------------------
@st.cache_data
def get_team_details(team_id: int):
    """
    Retrieve a user's team details from the FPL API given the team (entry) ID.
    """
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# -----------------------------------
# 3. ChatGPT API Integration Function (Updated for OpenAI v1.0+)
# -----------------------------------
def get_chatgpt_response(messages):
    """
    Call OpenAI's ChatCompletion API with a list of messages.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or another model you have access to
        messages=messages,
        temperature=0.7,
    )
    # Updated: Use .content instead of dictionary-style access
    reply = response.choices[0].message["content"]
    return reply

# -----------------------------------
# 4. Streamlit Interface Setup

# -----------------------------------
st.title("FPL Assistant Chatbot")

# Initialize conversation state if not already present
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": (
            "You are an expert Fantasy Premier League assistant. "
            "You provide detailed game data, player statistics, and personalized recommendations "
            "based on up-to-date FPL data. Analyze user teams and suggest optimal transfers "
            "or replacements to improve team performance."
        )}
    ]

# -----------------------------------
# 5. Chat Interface Section
# -----------------------------------
st.header("Chat with the FPL Assistant")
user_input = st.text_input("Enter your message:", key="chat_input")
if st.button("Send Message", key="send_chat") and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Generating response..."):
        assistant_reply = get_chatgpt_response(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.experimental_rerun()

# Display conversation history
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"**User:** {message['content']}")
    elif message["role"] == "assistant":
        st.markdown(f"**Assistant:** {message['content']}")

# -----------------------------------
# 6. Team Analysis Section
# -----------------------------------
st.header("Analyze Your Fantasy Team")

# Option 1: Manual Team Entry
st.markdown("**Option 1:** Enter your team details manually (e.g., a list of player names or IDs).")
user_team = st.text_area("Enter your team here:", key="team_input")

# Option 2: Fetch Team Automatically Using Team ID
st.markdown("**Option 2:** Enter your FPL team ID to automatically fetch your team details.")
team_id_input = st.text_input("Enter your FPL Team ID:", key="team_id")
if st.button("Fetch My Team", key="fetch_team") and team_id_input:
    try:
        team_id = int(team_id_input)
        fetched_team = get_team_details(team_id)
        if fetched_team:
            st.success(f"Successfully fetched team data for Team ID {team_id}!")
            st.json(fetched_team)
            # For analysis, we use the fetched team details as a string
            user_team = json.dumps(fetched_team, indent=2)
        else:
            st.error("Failed to fetch team data. Please check your team ID.")
    except ValueError:
        st.error("Invalid team ID. Please enter a numeric value.")

# Analyze team if input is provided either manually or fetched automatically
if st.button("Analyze Team", key="analyze_team") and user_team:
    analysis_prompt = (
        f"Using the latest Fantasy Premier League data, analyze the following team: {user_team}. "
        "Based on current gameweek statistics and upcoming fixtures, provide context-aware, data-driven insights "
        "and suggest the best possible transfers or replacements to improve team performance."
    )
    st.session_state.messages.append({"role": "user", "content": analysis_prompt})
    with st.spinner("Analyzing team and generating recommendations..."):
        team_analysis_reply = get_chatgpt_response(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": team_analysis_reply})
    st.experimental_rerun()
