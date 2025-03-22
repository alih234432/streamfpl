import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from config import OPENAI_API_KEY, LLM_MODEL
from fplcore.fixture import get_fixtures_summary, get_team_fixtures, extract_team_name
from fplcore.fpl_rules import find_rules_information

# Initialize OpenAI LLM with LangChain
llm = ChatOpenAI(model_name=LLM_MODEL, openai_api_key=OPENAI_API_KEY)

# Conversation Memory (Keeps chat context)
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    input_key="user_input",
    return_messages=True
)

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
    
    # Create a form that will submit when Enter is