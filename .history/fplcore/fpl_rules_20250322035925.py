import streamlit as st
import pandas as pd
import json
import os
import requests
from fplcore.logger import log_error, log_info

# Try to import BeautifulSoup, but don't fail if not available
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    log_error("BeautifulSoup not installed. Web scraping functionality will be disabled.")

from config import DATA_FOLDER

def ensure_rules_folder():
    """Create rules folder if it doesn't exist"""
    rules_folder = os.path.join(DATA_FOLDER, "rules")
    if not os.path.exists(rules_folder):
        os.makedirs(rules_folder)
    return rules_folder

def load_rules_file(file_name):
    """Load rules data from JSON file"""
    try:
        rules_folder = ensure_rules_folder()
        file_path = os.path.join(rules_folder, file_name)
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            log_error(f"Rules file not found: {file_path}")
            return {}
    except Exception as e:
        log_error(f"Error loading rules file {file_name}: {e}")
        return {}

def save_rules_file(data, file_name):
    """Save rules data to JSON file"""
    try:
        rules_folder = ensure_rules_folder()
        file_path = os.path.join(rules_folder, file_name)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        log_info(f"Saved rules data to {file_path}")
        return True
    except Exception as e:
        log_error(f"Error saving rules file {file_name}: {e}")
        return False

def load_default_rules():
    """Load default FPL rules from JSON file"""
    return load_rules_file("rules_default_rules.json")

def load_default_terminology():
    """Load default FPL terminology from JSON file"""
    return load_rules_file("rules_default_terminology.json")

def scrape_fpl_website():
    """Scrape rules from FPL website and save to separate files"""
    if not BEAUTIFULSOUP_AVAILABLE:
        st.warning("Web scraping is disabled because BeautifulSoup is not installed. Use pip install beautifulsoup4 to enable this feature.")
        return False

    urls = {
        "faqs": "https://fantasy.premierleague.com/help",
        "rules": "https://fantasy.premierleague.com/help/rules",
        "terms": "https://fantasy.premierleague.com/help/terms",
        "new": "https://fantasy.premierleague.com/help/new"
    }
    
    success = True
    
    for section, url in urls.items():
        try:
            log_info(f"Scraping FPL website section: {section} from {url}")
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main content div (adjust selector based on actual page structure)
            content_div = soup.find('div', class_='FplHelp')
            if not content_div:
                content_div = soup.find('div', class_='Prose')  # Try alternative selector
            
            if content_div:
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
                
                # Save to separate file
                file_name = f"rules_website_{section}.json"
                save_rules_file(section_content, file_name)
                log_info(f"Successfully scraped and saved {section} rules")
            else:
                log_error(f"Could not find content div in {section} page")
                success = False
                
                # Fallback: get all text from body
                body = soup.find('body')
                if body:
                    all_text = body.get_text().strip()
                    save_rules_file({"content": all_text}, f"rules_website_{section}.json")
                    log_info(f"Used fallback method for {section} rules")
        except Exception as e:
            log_error(f"Error scraping {section} rules: {e}")
            success = False
    
    return success

def load_all_website_rules():
    """Load all scraped website rules"""
    website_rules = {}
    for section in ['faqs', 'rules', 'terms', 'new']:
        file_name = f"rules_website_{section}.json"
        data = load_rules_file(file_name)
        if data:
            website_rules[section] = data
    
    return website_rules

def find_rules_information(query):
    """Search the FPL rules and terminology for relevant information"""
    query = query.lower()
    
    # Load rules data
    fpl_rules = load_default_rules()
    fpl_terminology = load_default_terminology()
    website_rules = load_all_website_rules()
    
    # Initialize the results
    results = []
    
    # Search in default FPL rules
    for category, content in fpl_rules.items():
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
    
    # Search in FPL terminology
    for term, definition in fpl_terminology.items():
        if query in term.lower() or query in definition.lower():
            results.append(f"Term: {term} - {definition}")
    
    # Search in website rules
    for section, section_data in website_rules.items():
        for heading, content in section_data.items():
            if isinstance(content, list):
                for item in content:
                    if query in item.lower():
                        results.append(f"FPL Website ({section.capitalize()}) - {heading}: {item}")
            elif isinstance(content, str):
                if query in content.lower():
                    results.append(f"FPL Website ({section.capitalize()}) - {heading}: {content[:200]}...")
    
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
        if keyword in query and section == "scoring" and "scoring" in fpl_rules:
            results.append(f"Complete Scoring Rules: {json.dumps(fpl_rules['scoring'], indent=2)}")
            break
    
    for keyword, section in keywords_to_sections.items():
        if keyword in query and section == "team_rules" and "team_rules" in fpl_rules:
            results.append(f"Complete Team Rules: {json.dumps(fpl_rules['team_rules'], indent=2)}")
            break
    
    return "\n\n".join(results) if results else "No specific FPL rules found for this query."

def rules_reference():
    """Display FPL rules and terminology reference"""
    st.title("FPL Rules & Terminology Reference")
    
    # Load the rules data
    fpl_rules = load_default_rules()
    fpl_terminology = load_default_terminology()
    website_rules = load_all_website_rules()
    
    # Check if we have website rules or offer to fetch them
    if not website_rules and BEAUTIFULSOUP_AVAILABLE:
        st.info("FPL website rules have not been fetched yet.")
        if st.button("Fetch Official FPL Rules from Website"):
            with st.spinner("Fetching rules from FPL website. This may take a moment..."):
                success = scrape_fpl_website()
                if success:
                    st.success("Successfully fetched rules from FPL website!")
                    website_rules = load_all_website_rules()  # Reload after fetching
                else:
                    st.error("Failed to fetch some rules from the FPL website.")
    
    # Create tabs for different categories
    tabs = ["Scoring", "Team Rules", "Other Rules", "Terminology"]
    
    # Add website rule tabs if available
    if website_rules:
        for section in website_rules.keys():
            tabs.append(f"FPL {section.capitalize()}")
    
    # Create the tabs
    tab_objects = st.tabs(tabs)
    
    # Scoring tab
    with tab_objects[0]:
        st.header("Scoring Rules")
        if "scoring" in fpl_rules:
            scoring = fpl_rules["scoring"]
            
            st.subheader("Appearance Points")
            st.write(scoring.get("playing", "Information not available"))
            
            st.subheader("Goals")
            for position, points in scoring.get("goals", {}).items():
                st.write(f"**{position.capitalize()}:** {points}")
            
            st.subheader("Clean Sheets")
            for position, points in scoring.get("clean_sheets", {}).items():
                st.write(f"**{position.capitalize()}:** {points}")
            
            st.subheader("Other Scoring")
            st.write(f"**Assists:** {scoring.get('assists', 'Information not available')}")
            st.write(f"**Saves:** {scoring.get('saves', 'Information not available')}")
            st.write(f"**Penalty Save:** {scoring.get('penalty_save', 'Information not available')}")
            st.write(f"**Penalty Miss:** {scoring.get('penalty_miss', 'Information not available')}")
            st.write(f"**Yellow Card:** {scoring.get('yellow_card', 'Information not available')}")
            st.write(f"**Red Card:** {scoring.get('red_card', 'Information not available')}")
            st.write(f"**Own Goal:** {scoring.get('own_goal', 'Information not available')}")
            st.write(f"**Bonus Points:** {scoring.get('bonus', 'Information not available')}")
        else:
            st.warning("Scoring rules data not available.")
    
    # Team Rules tab
    with tab_objects[1]:
        st.header("Team Rules")
        if "team_rules" in fpl_rules:
            team_rules = fpl_rules["team_rules"]
            
            st.write(f"**Budget:** {team_rules.get('budget', 'Information not available')}")
            st.write(f"**Squad Size:** {team_rules.get('squad_size', 'Information not available')}")
            st.write(f"**Formation:** {team_rules.get('formation', 'Information not available')}")
            st.write(f"**Captaincy:** {team_rules.get('captaincy', 'Information not available')}")
            st.write(f"**Transfers:** {team_rules.get('transfers', 'Information not available')}")
            st.write(f"**Team Limit:** {team_rules.get('team_limit', 'Information not available')}")
            
            st.subheader("Chips")
            for chip, description in team_rules.get("chips", {}).items():
                st.write(f"**{chip.capitalize()}:** {description}")
        else:
            st.warning("Team rules data not available.")
    
    # Other Rules tab
    with tab_objects[2]:
        st.header("Other Important Rules")
        st.write(f"**Deadlines:** {fpl_rules.get('deadlines', 'Information not available')}")
        st.write(f"**Price Changes:** {fpl_rules.get('price_changes', 'Information not available')}")
        st.write(f"**Wildcards:** {fpl_rules.get('wildcards', 'Information not available')}")
        st.write(f"**Double Gameweeks:** {fpl_rules.get('double_gameweeks', 'Information not available')}")
        st.write(f"**Blank Gameweeks:** {fpl_rules.get('blank_gameweeks', 'Information not available')}")
    
    # Terminology tab
    with tab_objects[3]:
        st.header("FPL Terminology")
        
        # Convert terminology to DataFrame for easier display
        terms_data = [{"Term": term, "Definition": definition} for term, definition in fpl_terminology.items()]
        terms_df = pd.DataFrame(terms_data)
        
        # Add a search box
        search = st.text_input("Search terminology:")
        if search:
            filtered_df = terms_df[terms_df["Term"].str.contains(search, case=False) | 
                                  terms_df["Definition"].str.contains(search, case=False)]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(terms_df, use_container_width=True)
    
    # Website rules tabs
    if website_rules:
        for i, section in enumerate(website_rules.keys()):
            with tab_objects[4 + i]:
                st.header(f"FPL {section.capitalize()}")
                
                # Display the content
                section_data = website_rules[section]
                
                # Create a selectbox for the headings
                headings = list(section_data.keys())
                if headings:
                    selected_heading = st.selectbox(f"Choose a {section} topic:", headings, key=f"select_{section}")
                    
                    # Display the content for the selected heading
                    content = section_data.get(selected_heading, [])
                    if isinstance(content, list):
                        for item in content:
                            st.write(item)
                    else:
                        st.write(content)
                else:
                    st.warning(f"No {section} content available.")