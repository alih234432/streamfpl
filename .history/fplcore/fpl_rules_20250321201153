import streamlit as st
import pandas as pd
import json

# FPL Rules Database
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

# FPL Terminology Database
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