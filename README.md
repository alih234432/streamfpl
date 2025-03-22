# FPL Chatbot

A Fantasy Premier League (FPL) chatbot built with Streamlit and AI that provides insights, fixture analysis, and personalized advice for FPL managers.

## Features

- **AI Chatbot**: Get answers to any FPL question using natural language
- **Team Advice**: Personalized suggestions for your FPL team
- **Fixture Analysis**: Upcoming matches and difficulty ratings
- **Rules Reference**: Complete FPL rules and terminology
- **Notifications**: Latest injury updates and price changes

## Project Structure

```
fpl_chatbot/
├── README.md
├── requirements.txt
├── .gitignore
├── app.py                  # Main entry point (Streamlit front-end)
├── config.py               # Global configuration (API keys, settings, etc.)
├── data/                   # Data sources and files
│   ├── players.csv
│   ├── fixtures.json
│   └── ...
└── fplcore/                # All Python source files related to the FPL application
    ├── __init__.py
    ├── players.py          # Functions/classes related to players
    ├── user.py             # User management and interactions
    ├── fixture.py          # Fixture handling and analysis
    ├── fpl_rules.py        # FPL rules and validations
    ├── chatbot.py          # Chatbot logic (NLP, conversation flow, etc.)
    ├── logger.py           # Logging configuration and setup
    └── helpers.py          # Utility functions and helpers
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fpl_chatbot.git
cd fpl_chatbot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
```

## Usage

Run the application:
```bash
streamlit run app.py
```

Navigate to the provided URL (usually http://localhost:8501) in your web browser.

## API Sources

The application uses the official Fantasy Premier League API endpoints:
- https://fantasy.premierleague.com/api/bootstrap-static/
- https://fantasy.premierleague.com/api/fixtures/
- https://fantasy.premierleague.com/api/element-summary/{player_id}/
- https://fantasy.premierleague.com/api/entry/{team_id}/

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.