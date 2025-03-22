import json
import os
import requests
from bs4 import BeautifulSoup

from config import DATA_FOLDER
from fplcore.logger import log_info, log_error
from fplcore.fpl_rules import ensure_data_folder, save_rules_data

def initialize_all_data():
    """Initialize all required data files for the application"""
    log_info("Initializing application data...")
    
    # Create data folder if it doesn't exist
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        log_info(f"Created data folder: {DATA_FOLDER}")
    
    # Initialize rules data
    initialize_rules_data()
    
    # Scrape FPL website rules
    try:
        scrape_fpl_website_rules()
    except Exception as e:
        log_error(f"Error scraping FPL website rules: {e}")
    
    log_info("Data initialization complete.")

def initialize_rules_data():
    """Initialize rules and terminology JSON files"""
    rules_folder = ensure_data_folder()
    
    # Default FPL rules
    fpl_rules = {
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
    
    # Default FPL terminology
    fpl_terminology = {
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
    
    # Save files if they don't exist
    if not os.path.exists(os.path.join(rules_folder, "fpl_rules.json")):
        save_rules_data(fpl_rules, "fpl_rules.json")
        log_info("Created default FPL rules file")
    
    if not os.path.exists(os.path.join(rules_folder, "fpl_terminology.json")):
        save_rules_data(fpl_terminology, "fpl_terminology.json")
        log_info("Created default FPL terminology file")

def scrape_fpl_website_rules():
    """Scrape rules from FPL website pages"""
    urls = {
        "help": "https://fantasy.premierleague.com/help",
        "rules": "https://fantasy.premierleague.com/help/rules",
        "terms": "https://fantasy.premierleague.com/help/terms",
        "new_features": "https://fantasy.premierleague.com/help/new"
    }
    
    rules_folder = ensure_data_folder()
    all_rules = {}
    
    for section, url in urls.items():
        log_info(f"Scraping FPL rules from {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main content div (adjust selector based on actual page structure)
            content_div = soup.find('div', class_='Help')  # This selector may need adjustment
            
            if not content_div:
                content_div = soup.find('div', class_='Prose')  # Try alternative selector
            
            if content_div:
                # Extract structured content
                section_content = {}
                
                # Get all headings
                headings = content_div.find_all(['h1', 'h2', 'h3'])
                
                for heading in headings:
                    heading_text = heading.get_text().strip()
                    section_content[heading_text] = []
                    
                    # Get all content until the next heading
                    current = heading.next_sibling
                    while current and (not current.name or current.name not in ['h1', 'h2', 'h3']):
                        if current.name == 'p' or current.name == 'li':
                            text = current.get_text().strip()
                            if text:
                                section_content[heading_text].append(text)
                        elif current.name == 'ul' or current.name == 'ol':
                            for li in current.find_all('li'):
                                text = li.get_text().strip()
                                if text:
                                    section_content[heading_text].append(f"• {text}")
                        current = current.next_sibling
                
                all_rules[section] = section_content
                log_info(f"Successfully scraped {section} rules")
            else:
                log_error(f"Could not find content div in {section} page")
                
                # Fallback: get all text from body
                body = soup.find('body')
                if body:
                    all_rules[section] = {"Content": body.get_text().strip()}
                    log_info(f"Used fallback method for {section} rules")
        except Exception as e:
            log_error(f"Error scraping {section} rules: {e}")
    
    # Save all scraped rules
    if all_rules:
        file_path = os.path.join(rules_folder, "fpl_website_rules.json")
        with open(file_path, 'w') as f:
            json.dump(all_rules, f, indent=2)
        log_info(f"Saved all scraped FPL rules to {file_path}")
    
    return all_rules

# Run data initialization if this module is executed directly
if __name__ == "__main__":
    initialize_all_data()