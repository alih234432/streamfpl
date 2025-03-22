import streamlit as st
import pandas as pd
import json
import os
import requests
from bs4 import BeautifulSoup
import re

from config import DATA_FOLDER
from fplcore.logger import log_error, log_info

def ensure_data_folder():
    """Create data folder if it doesn't exist"""
    rules_folder = os.path.join(DATA_FOLDER, "rules")
    if not os.path.exists(rules_folder):
        os.makedirs(rules_folder)
    return rules_folder

def load_rules_data(file_name):
    """Load rules data from JSON file, creating default if not exists"""
    rules_folder = ensure_data_folder()
    file_path = os.path.join(rules_folder, file_name)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        # Return empty data if file doesn't exist
        return {}

def save_rules_data(data, file_name):
    """Save rules data to JSON file"""
    rules_folder = ensure_data_folder()
    file_path = os.path.join(rules_folder, file_name)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    log_info(f"Saved rules data to {file_path}")

def scrape_fpl_rules():
    """Scrape rules from FPL website and convert to structured data"""
    urls = {
        "help": "https://fantasy.premierleague.com/help",
        "rules": "https://fantasy.premierleague.com/help/rules",
        "terms": "https://fantasy.premierleague.com/help/terms",
        "new_features": "https://fantasy.premierleague.com/help/new"
    }
    
    rules_data = {}
    
    for section, url in urls.items():
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content - adjust selectors based on actual website structure
            content_div = soup.find('div', class_='FplHelp')
            
            if content_div:
                # Process different sections differently
                if section == "rules":
                    rules_data[section] = extract_structured_rules(content_div)
                else:
                    # For other sections, just get all text
                    rules_data[section] = extract_text_content(content_div)
                    
                log_info(f"Successfully scraped {section} rules")
            else:
                log_error(f"Could not find content div in {section} page")
                
        except Exception as e:
            log_error(f"Error scraping {section} rules: {e}")
    
    # Save the scraped data
    save_rules_data(rules_data, "fpl_website_rules.json")
    return rules_data

def extract_structured_rules(content_div):
    """Extract rules in a structured format from the rules page"""
    structured_rules = {}
    
    # Find all sections (h2 or h3 tags)
    sections = content_div.find_all(['h2', 'h3'])
    
    for section in sections:
        section_title = section.text.strip()
        section_content = []
        
        # Get all content until the next section
        next_element = section.next_sibling
        while next_element and next_element.name not in ['h2', 'h3']:
            if next_element.name == 'p':
                section_content.append(next_element.text.strip())
            elif next_element.name == 'ul':
                for li in next_element.find_all('li'):
                    section_content.append(f"• {li.text.strip()}")
            next_element = next_element.next_sibling
        
        structured_rules[section_title] = section_content
    
    return structured_rules

def extract_text_content(content_div):
    """Extract all text content from a div"""
    text_content = {}
    
    # Find all sections (h2 or h3 tags)
    sections = content_div.find_all(['h2', 'h3'])
    
    for section in sections:
        section_title = section.text.strip()
        section_text = []
        
        # Get all text until the next section
        next_element = section.next_sibling
        while next_element and next_element.name not in ['h2', 'h3']:
            if hasattr(next_element, 'text'):
                text = next_element.text.strip()
                if text:
                    section_text.append(text)
            next_element = next_element.next_sibling
        
        text_content[section_title] = " ".join(section_text)
    
    return text_content

def initialize_default_rules():
    """Initialize default rules data if not already present"""
    rules_folder = ensure_data_folder()
    
    # Define default FPL rules
    fpl_rules = {
        "scoring": {
            "playing": "Players who play up to 60 minutes get 1 point. Players who play 60+ minutes get 2 points.",
            "goals": {
                "forward": "Forwards get 4 points per goal scored.",
                "midfielder": "Midfielders get 5 points per goal scored.",
                "defender": "Defenders get 6 points per goal scored.",
                "goalkeeper": "Goalkeepers get 6 points per goal scored."
            },
            # ... (rest of the scoring rules)
        },
        "team_rules": {
            "budget": "£100 million initial budget to build your squad.",
            "squad_size": "15 players total: 2 goalkeepers, 5 defenders, 5 midfielders, and 3 forwards.",
            # ... (rest of the team rules)
        },
        # ... (rest of the rules)
    }
    
    # Define default FPL terminology
    fpl_terminology = {
        "BGW": "Blank Gameweek - when teams have no fixture in a gameweek.",
        "DGW": "Double Gameweek - when teams play twice in a single gameweek.",
        # ... (rest of the terminology)
    }
    
    # Save default data if files don't exist
    if not os.path.exists(os.path.join(rules_folder, "fpl_rules.json")):
        save_rules_data(fpl_rules, "fpl_rules.json")
    
    if not os.path.exists(os.path.join(rules_folder, "fpl_terminology.json")):
        save_rules_data(fpl_terminology, "fpl_terminology.json")
    
    # Try to scrape website rules if that file doesn't exist
    if not os.path.exists(os.path.join(rules_folder, "fpl_website_rules.json")):
        try:
            scrape_fpl_rules()
        except Exception as e:
            log_error(f"Error scraping FPL website rules: {e}")

def find_rules_information(query):
    """Search the FPL rules and terminology for relevant information"""
    query = query.lower()
    
    # Load rules data
    fpl_rules = load_rules_data("fpl_rules.json")
    fpl_terminology = load_rules_data("fpl_terminology.json")
    fpl_website_rules = load_rules_data("fpl_website_rules.json")
    
    # Initialize the results
    results = []
    
    # Search in FPL_RULES (exact and partial matches)
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
    
    # Search in FPL_TERMINOLOGY
    for term, definition in fpl_terminology.items():
        if query in term.lower() or query in definition.lower():
            results.append(f"Term: {term} - {definition}")
    
    # Search in website rules
    for section, content in fpl_website_rules.items():
        if isinstance(content, dict):
            for subsection, subsection_content in content.items():
                if isinstance(subsection_content, list):
                    # Content is a list of paragraphs
                    for paragraph in subsection_content:
                        if query in paragraph.lower():
                            results.append(f"Official FPL Rules - {subsection}: {paragraph}")
                elif isinstance(subsection_content, str):
                    # Content is a single string
                    if query in subsection.lower() or query in subsection_content.lower():
                        results.append(f"Official FPL Rules - {subsection}: {subsection_content[:200]}...")
        elif isinstance(content, str):
            if query in section.lower() or query in content.lower():
                results.append(f"Official FPL: {section} - {content[:200]}...")
    
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
    fpl_rules = load_rules_data("fpl_rules.json")
    fpl_terminology = load_rules_data("fpl_terminology.json")
    fpl_website_rules = load_rules_data("fpl_website_rules.json")
    
    # Create tabs for different categories
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Scoring", "Team Rules", "Other Rules", "Terminology", "Official FPL Rules"])
    
    with tab1:
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
    
    with tab2:
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
    
    with tab3:
        st.header("Other Important Rules")
        st.write(f"**Deadlines:** {fpl_rules.get('deadlines', 'Information not available')}")
        st.write(f"**Price Changes:** {fpl_rules.get('price_changes', 'Information not available')}")
        st.write(f"**Wildcards:** {fpl_rules.get('wildcards', 'Information not available')}")
        st.write(f"**Double Gameweeks:** {fpl_rules.get('double_gameweeks', 'Information not available')}")
        st.write(f"**Blank Gameweeks:** {fpl_rules.get('blank_gameweeks', 'Information not available')}")
    
    with tab4:
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
            
    with tab5:
        st.header("Official FPL Rules")
        
        # Show official rules from website
        if fpl_website_rules:
            sections = list(fpl_website_rules.keys())
            selected_section = st.selectbox("Select section:", sections)
            
            if selected_section in fpl_website_rules:
                content = fpl_website_rules[selected_section]
                
                if isinstance(content, dict):
                    subsections = list(content.keys())
                    selected_subsection = st.selectbox("Select subsection:", subsections)
                    
                    if selected_subsection in content:
                        subsection_content = content[selected_subsection]
                        
                        if isinstance(subsection_content, list):
                            for paragraph in subsection_content:
                                st.write(paragraph)
                        else:
                            st.write(subsection_content)
                else:
                    st.write(content)
        else:
            st.warning("Official rules data not available.")
            if st.button("Fetch Official Rules"):
                with st.spinner("Fetching rules from FPL website..."):
                    scrape_fpl_rules()
                st.success("Rules fetched successfully! Refresh this page to view them.")

# Initialize the rules data when the module is loaded
initialize_default_rules()