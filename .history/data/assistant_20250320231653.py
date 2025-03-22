import openai
import pandas as pd
from data.players import preprocess_player_data, get_current_gameweek
from data.team_analyzer import analyze_user_team

def get_assistant_response(prompt, fpl_data=None, fixtures_data=None, user_team=None, api_key=None):
    """Send the user's query to the ChatGPT API with FPL context."""
    
    # Set OpenAI API key if provided
    if api_key:
        openai.api_key = api_key
    
    # Add FPL data context to the prompt
    if fpl_data:
        # Preprocess and get current gameweek
        players_df = preprocess_player_data(fpl_data)
        events = fpl_data['events']
        current_gw = get_current_gameweek(events)
        
        # Get top performers
        top_scorers = players_df.sort_values('total_points', ascending=False).head(5)
        top_value = players_df.sort_values('value', ascending=False).head(5)
        
        # Add context about the data
        context = f"""
        You are an FPL Assistant with access to the latest Fantasy Premier League data.
        
        Current Gameweek: {current_gw}
        
        Top Point Scorers:
        {top_scorers[['web_name', 'team_name', 'total_points']].to_string(index=False)}
        
        Best Value Players:
        {top_value[['web_name', 'team_name', 'value', 'now_cost']].rename(columns={'now_cost': 'cost'}).to_string(index=False)}
        """
        
        # Add user team context if available
        if user_team:
            team_analysis = analyze_user_team(user_team, players_df)
            
            context += f"""
            User's Team Analysis:
            Team Value: £{team_analysis['metrics']['total_value']}m
            Total Points: {team_analysis['metrics']['total_points']}
            
            Potential Improvements:
            """
            
            for player, replacements in team_analysis['replacements'].items():
                context += f"Consider replacing {player} with one of: {', '.join(replacements)}\n"
        
        # Combine context with the user's question
        full_prompt = context + "\n\nUser Question: " + prompt
    else:
        full_prompt = prompt
    
    try:
        # Make API call to ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Fantasy Premier League assistant."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error getting response: {str(e)}"