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

# ---------------------------- FPL RULES & TERMINOLOGY DATABASE ----------------------------
FPL_RULES = {
    "scoring": {
        "playing": "Players who play up to 60 minutes get 1 point. Players who play 60+ minutes get 2 points.",
        "goals": {
            "forward": "Forwards get 4 points per goal scored.",
            "midfielder": "Midfielders get 5 points per goal scored.",
            "defender": "Defenders get 6 points per goal scored.",
            "goalkeeper": "Goalkeepers get 6 points per goal scored."
        },
        "assists": "All players get 3 points per assist.",
        "clean_sheets": {
            "defender": "Defenders get 4 points for a clean sheet.",
            "goalkeeper": "Goalkeepers get 4 points for a clean sheet.",
            "midfielder": "Midfielders get 1 point for a clean sheet.",
            "forward": "Forwards don't get points for clean sheets."
        },
        "saves": "Goalkeepers get 1 point for every 3 saves made.",
        "penalty_save": "5 points for saving a penalty.",
        "penalty_miss": "-2 points for missing a penalty.",
        "yellow_card": "-1 point for receiving a yellow card.",
        "red_card": "-3 points for receiving a red card.",
        "own_goal": "-2 points for scoring an own goal.",
        "bonus": "1-3 bonus points awarded to the best performing players in each match."
    },
    "team_rules": {
        "budget": "£100 million initial budget to build your squad.",
        "squad_size": "15 players total: 2 goalkeepers, 5 defenders, 5 midfielders, and 3 forwards.",
        "formation": "Must play a valid formation with 1 goalkeeper, at least 3 defenders, at least 2 midfielders, and at least 1 forward.",
        "captaincy": "Captain scores double points. Vice-captain is automatic replacement if captain doesn't play.",
        "transfers": "1 free transfer per gameweek. Additional transfers cost 4 points each.",
        "chips": {
            "wildcard": "Unlimited transfers in a single gameweek without point deductions. Can be used twice per season (once in each half).",
            "free_hit": "Temporary wildcard for a single gameweek. Team reverts to previous gameweek's team afterward.",
            "bench_boost": "Points scored by bench players are included in the gameweek's total.",
            "triple_captain": "Captain scores triple points instead of double for the gameweek."
        },
        "team_limit": "Maximum of 3 players from any single Premier League team."
    },
    "deadlines": "Team changes must be confirmed before the gameweek deadline (90 minutes before the first match of the gameweek).",
    "price_changes": "Player prices change based on transfer activity. Players can rise or fall by up to £0.3m per gameweek.",
    "wildcards": "2 wildcards per season: 1 to use before gameweek 20 deadline, and 1 to use after gameweek 20 deadline.",
    "double_gameweeks": "Some teams play twice in a single gameweek due to rescheduled fixtures.",
    "blank_gameweeks": "Some teams don't play in certain gameweeks due to fixture clashes with other competitions.",
}

FPL_TERMINOLOGY = {
    "BGW": "Blank Gameweek - when teams have no fixture in a gameweek.",
    "DGW": "Double Gameweek - when teams play twice in a single gameweek.",
    "TGW": "Triple Gameweek - rare occurrence when a team plays three matches in a single gameweek.",
    "OOP": "Out of Position - a player listed in one position but playing in a more advanced role.",
    "ICT Index": "Influence, Creativity, Threat Index - statistical metric to help make transfer decisions.",
    "xG": "Expected Goals - statistical measure of the quality of goal-scoring chances.",
    "xA": "Expected Assists - statistical measure of the quality of chances created.",
    "EO": "Effective Ownership - percentage of active teams in which a player's points count.",
    "TC": "Triple Captain - chip that triples captain's points for one gameweek.",
    "BB": "Bench Boost - chip that counts bench players' points for one gameweek.",
    "FH": "Free Hit - chip that allows temporary unlimited transfers for one gameweek.",
    "WC": "Wildcard - chip that allows unlimited transfers without point penalties.",
    "xMins": "Expected Minutes - predicted playing time for a player.",
    "Autosubs": "Automatic substitutions - bench players automatically replace starters who don't play.",
    "Hit": "Taking a hit - making extra transfers beyond the free transfer, costing 4 points each.",
    "Price Rise/Fall": "When players' values increase or decrease based on transfer activity.",
    "Differential": "Player with low ownership percentage who could give you an advantage.",
    "Template": "Common player selections found in many FPL teams.",
    "Set and Forget": "Selecting a player/team and keeping them regardless of fixtures.",
    "Knee-jerk": "Making impulsive transfers based on recent performance without considering long-term value.",
    "Gandhi Rule": "Unofficial rule suggesting not to captain players in early kickoff matches.",
    "Form": "A player's recent performance level, often measured by points in last 5 gameweeks.",
    "Fixtures": "Upcoming matches for a team, rated by difficulty.",
    "Squad Value": "Total market value of all players in your team.",
    "Team Value": "Amount available to spend if you sold all your players (purchase price + profit).",
    "ITB": "In The Bank - money not spent on your squad, available for future transfers.",
    "Bandwagon": "When many managers transfer in the same player after good performances.",
    "Essential": "Players considered must-haves due to form, fixtures, or value."
}

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

# ---------------------------- FPL RULE SEARCH ----------------------------
def find_rules_information(query):
    """Search the FPL rules and terminology for relevant information"""
    query = query.lower()
    
    # Initialize the results
    results = []
    
    # Search in FPL_RULES (exact and partial matches)
    for category, content in FPL_RULES.items():
        if isinstance(content, dict):
            for subcategory, subcontent in content.items():
                if isinstance(subcontent, dict):
                    for sub_subcategory, sub_subcontent in subcontent.items():
                        if query in sub_subcategory.lower() or query in sub_subcontent.lower():
                            results.append(f"{category.capitalize()} - {subcategory.capitalize()} - {sub_subcategory.capitalize()}: {sub_subcontent}")
                else:
                    if query in subcategory.lower() or query in str(subcontent).lower():
                        results.append(f"{category.capitalize()} - {subcategory.capitalize()}: {subcontent}")
        else:
            if query in category.lower() or query in str(content).lower():
                results.append(f"{category.capitalize()}: {content}")
    
    # Search in FPL_TERMINOLOGY
    for term, definition in FPL_TERMINOLOGY.items():
        if query in term.lower() or query in definition.lower():
            results.append(f"Term: {term} - {definition}")
    
    # If specific keywords are mentioned, add relevant complete sections
    keywords_to_sections = {
        "point": "scoring",
        "score": "scoring",
        "goal": "scoring",
        "assist": "scoring",
        "clean sheet": "scoring",
        "yellow": "scoring",
        "red card": "scoring",
        "bonus": "scoring",
        "budget": "team_rules",
        "squad": "team_rules",
        "formation": "team_rules",
        "captain": "team_rules",
        "transfer": "team_rules",
        "chip": "team_rules",
        "wildcard": "team_rules",
        "free hit": "team_rules",
        "bench boost": "team_rules",
        "triple captain": "team_rules"
    }
    
    for keyword, section in keywords_to_sections.items():
        if keyword in query and section == "scoring":
            results.append(f"Complete Scoring Rules: {json.dumps(FPL_RULES['scoring'], indent=2)}")
            break
    
    for keyword, section in keywords_to_sections.items():
        if keyword in query and section == "team_rules":
            results.append(f"Complete Team Rules: {json.dumps(FPL_RULES['team_rules'], indent=2)}")
            break
    
    return "\n\n".join(results) if results else "No specific FPL rules found for this query."

# ---------------------------- CHATBOT MODULE WITH FIXTURES AND RULES INTEGRATION ----------------------------
# Enhanced prompt template with fixture knowledge and FPL rules
chat_prompt = PromptTemplate(
    input_variables=["chat_history", "user_input", "fixtures_data", "rules_data"],
    template="""
    You are an AI assistant specialized in Fantasy Premier League (FPL).
    You are an expert on all FPL rules, strategies, and terminology.
    Answer user queries based on current fixtures, injuries, team management, and official FPL rules.
    
    Here is the latest fixture information:
    {fixtures_data}
    
    Here are the relevant FPL rules and terminology for this query:
    {rules_data}
    
    Chat History:
    {chat_history}
    
    User: {user_input}
    AI:
    """
)

# Create an AI Chain for structured interaction
chat_chain = LLMChain(llm=llm, prompt=chat_prompt, memory=memory)

def chat_with_gpt(user_input):
    """Processes user queries using LangChain AI Chain with fixtures data and FPL rules"""
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
    
    # Search for relevant FPL rules information
    rules_data = find_rules_information(user_input)
    
    # Get response from the AI
    response = chat_chain.run(
        user_input=user_input, 
        fixtures_data=fixtures_data,
        rules_data=rules_data
    )
    
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
    """Handles AI chatbot interactions with memory, fixtures data, and FPL rules"""
    st.title("FPL AI Chatbot")
    st.write("Ask me anything about Fantasy Premier League including fixtures, rules, and strategies!")

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

# ---------------------------- FIXTURE ANALYSIS MODULE ----------------------------
def fixture_analysis(weeks=5):
    """Analyze upcoming fixtures for difficulty and double gameweeks"""
    st.title("Fixture Analysis")
    
    # Get current gameweek
    current_gw = get_current_gameweek()
    if not current_gw:
        st.error("Could not determine current gameweek.")
        return
    
    # Get fixtures for the specified number of gameweeks
    all_fixtures = []
    for gw in range(current_gw, current_gw + weeks):
        gw_fixtures = get_fixtures_for_gameweek(gw)
        all_fixtures.extend(gw_fixtures)
    
    # Analyze for double gameweeks
    gw_team_count = {}
    for fixture in all_fixtures:
        gw = fixture['gameweek']
        home_team = fixture['home_team']
        away_team = fixture['away_team']
        
        if gw not in gw_team_count:
            gw_team_count[gw] = {}
        
        if home_team not in gw_team_count[gw]:
            gw_team_count[gw][home_team] = 0
        if away_team not in gw_team_count[gw]:
            gw_team_count[gw][away_team] = 0
        
        gw_team_count[gw][home_team] += 1
        gw_team_count[gw][away_team] += 1
    
    # Display double gameweeks if any
    dgw_found = False
    for gw, teams in gw_team_count.items():
        double_gw_teams = [team for team, count in teams.items() if count > 1]
        if double_gw_teams:
            if not dgw_found:
                st.subheader("Double Gameweeks")
                dgw_found = True
            st.write(f"Gameweek {gw}: {', '.join(double_gw_teams)}")
    
    if not dgw_found:
        st.info("No double gameweeks found in the analyzed period.")
    
    # Display the full fixture table
    st.subheader("Upcoming Fixtures")
    
    # Convert to DataFrame for easier display
    fixture_data = []
    for fixture in all_fixtures:
        fixture_data.append({
            'Gameweek': fixture['gameweek'],
            'Home Team': fixture['home_team'],
            'Away Team': fixture['away_team'],
            'Date & Time': fixture['kickoff_time']
        })
    
    fixture_df = pd.DataFrame(fixture_data)
    st.dataframe(fixture_df)

# ---------------------------- FPL RULES REFERENCE MODULE ----------------------------
def rules_reference():
    """Display FPL rules and terminology reference"""
    st.title("FPL Rules & Terminology Reference")
    
    # Create tabs for different categories
    tab1, tab2, tab3, tab4 = st.tabs(["Scoring", "Team Rules", "Other Rules", "Terminology"])
    
    with tab1:
        st.header("Scoring Rules")
        st.subheader("Appearance Points")
        st.write(FPL_RULES["scoring"]["playing"])
        
        st.subheader("Goals")
        for position, points in FPL_RULES["scoring"]["goals"].items():
            st.write(f"**{position.capitalize()}:** {points}")
        
        st.subheader("Clean Sheets")
        for position, points in FPL_RULES["scoring"]["clean_sheets"].items():
            st.write(f"**{position.capitalize()}:** {points}")
        
        st.subheader("Other Scoring")
        st.write(f"**Assists:** {FPL_RULES['scoring']['assists']}")
        st.write(f"**Saves:** {FPL_RULES['scoring']['saves']}")
        st.write(f"**Penalty Save:** {FPL_RULES['scoring']['penalty_save']}")
        st.write(f"**Penalty Miss:** {FPL_RULES['scoring']['penalty_miss']}")
        st.write(f"**Yellow Card:** {FPL_RULES['scoring']['yellow_card']}")
        st.write(f"**Red Card:** {FPL_RULES['scoring']['red_card']}")
        st.write(f"**Own Goal:** {FPL_RULES['scoring']['own_goal']}")
        st.write(f"**Bonus Points:** {FPL_RULES['scoring']['bonus']}")
    
    with tab2:
        st.header("Team Rules")
        st.write(f"**Budget:** {FPL_RULES['team_rules']['budget']}")
        st.write(f"**Squad Size:** {FPL_RULES['team_rules']['squad_size']}")
        st.write(f"**Formation:** {FPL_RULES['team_rules']['formation']}")
        st.write(f"**Captaincy:** {FPL_RULES['team_rules']['captaincy']}")
        st.write(f"**Transfers:** {FPL_RULES['team_rules']['transfers']}")
        st.write(f"**Team Limit:** {FPL_RULES['team_rules']['team_limit']}")
        
        st.subheader("Chips")
        for chip, description in FPL_RULES["team_rules"]["chips"].items():
            st.write(f"**{chip.capitalize()}:** {description}")
    
    with tab3:
        st.header("Other Important Rules")
        st.write(f"**Deadlines:** {FPL_RULES['deadlines']}")
        st.write(f"**Price Changes:** {FPL_RULES['price_changes']}")
        st.write(f"**Wildcards:** {FPL_RULES['wildcards']}")
        st.write(f"**Double Gameweeks:** {FPL_RULES['double_gameweeks']}")
        st.write(f"**Blank Gameweeks:** {FPL_RULES['blank_gameweeks']}")
    
    with tab4:
        st.header("FPL Terminology")
        
        # Convert terminology to DataFrame for easier display
        terms_data = [{"Term": term, "Definition": definition} for term, definition in FPL_TERMINOLOGY.items()]
        terms_df = pd.DataFrame(terms_data)
        
        # Add a search box
        search = st.text_input("Search terminology:")
        if search:
            filtered_df = terms_df[terms_df["Term"].str.contains(search, case=False) | 
                                  terms_df["Definition"].str.contains(search, case=False)]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(terms_df, use_container_width=True)

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

# ---------------------------- RUN THE APP ----------------------------
if __name__ == "__main__":
    if "authenticated" not in st.session_state:
        login()
    main()  # Always call main() to show navigation