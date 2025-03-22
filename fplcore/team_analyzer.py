def analyze_user_team(team_ids, all_players):
    """Analyze the user's team and suggest improvements."""
    team_df = all_players[all_players['id'].isin(team_ids)].copy()
    
    # Calculate team metrics
    total_value = team_df['now_cost'].sum() / 10  # Convert to display format
    total_points = team_df['total_points'].sum()
    avg_minutes = team_df['minutes'].mean()
    
    # Find underperforming players (below median value)
    median_value = team_df['value'].median()
    underperforming = team_df[team_df['value'] < median_value].sort_values('value')
    
    # Find potential replacements for each underperforming player
    replacements = {}
    for _, player in underperforming.iterrows():
        position = player['position']
        budget = (player['now_cost'] + 5) / 10  # Allow for 0.5 more
        
        # Import locally to avoid circular imports
        from fplcore.players import get_player_recommendations
        
        better_options = get_player_recommendations(
            all_players, 
            position=position, 
            budget=budget, 
            count=3
        )
        
        # Only recommend players not already in the team
        better_options = better_options[~better_options['id'].isin(team_ids)]
        
        if not better_options.empty:
            replacements[player['web_name']] = better_options['web_name'].tolist()
    
    return {
        "metrics": {
            "total_value": total_value,
            "total_points": total_points,
            "avg_minutes": avg_minutes
        },
        "underperforming": underperforming['web_name'].tolist(),
        "replacements": replacements
    }