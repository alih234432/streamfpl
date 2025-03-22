import pandas as pd

def get_current_gameweek(events_data):
    """Determine the current gameweek."""
    for event in events_data:
        if event['is_current']:
            return event['id']
    # If no current gameweek found, return the next one
    for event in events_data:
        if event['is_next']:
            return event['id']
    return 1  # Default to 1 if nothing found

def preprocess_player_data(data):
    """Transform raw FPL data into a more usable player dataframe."""
    players = data['elements']
    teams = {team['id']: team['name'] for team in data['teams']}
    positions = {pos['id']: pos['singular_name'] for pos in data['element_types']}
    
    player_df = pd.DataFrame(players)
    
    # Add team name and position
    player_df['team_name'] = player_df['team'].map(teams)
    player_df['position'] = player_df['element_type'].map(positions)
    
    # Calculate points per game and value (points per cost)
    player_df['value'] = player_df['total_points'] / player_df['now_cost']
    
    # Filter to only include players who have played
    active_players = player_df[player_df['minutes'] > 0].copy()
    
    return active_players

def get_player_recommendations(player_df, position=None, budget=None, count=5):
    """Get player recommendations based on position and budget constraints."""
    filtered_df = player_df.copy()
    
    if position:
        filtered_df = filtered_df[filtered_df['position'] == position]
    
    if budget:
        # Convert budget to FPL format (multiply by 10)
        budget_internal = float(budget) * 10
        filtered_df = filtered_df[filtered_df['now_cost'] <= budget_internal]
    
    # Sort by value (points per cost)
    filtered_df = filtered_df.sort_values('value', ascending=False)
    
    return filtered_df.head(count)

def get_top_performers(player_df, category='total_points', count=10):
    """Get top performing players by a specific category."""
    return player_df.sort_values(category, ascending=False).head(count)