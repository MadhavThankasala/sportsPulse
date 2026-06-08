---

## How the Agent Works

SportsPulse uses a multi-step agentic loop with 4 tools:

| Tool | What It Does |
|---|---|
| get_team_sponsors | Queries MongoDB for sponsor-ticker relationships |
| get_historical_pattern | Retrieves avg price movement from 64 historical data points |
| get_current_stock_price | Fetches live price via Yahoo Finance |
| save_signal_report | Persists report with vector embedding to MongoDB |

The agent autonomously decides which tools to call, in what order, and how many times — reasoning across all data sources before generating the final report.

---

## MongoDB Usage

MongoDB Atlas serves three distinct roles in this project:

**1. Sponsor Knowledge Graph**
Stores team-sponsor-ticker relationships as nested documents. Enables instant lookup of which publicly traded companies are financially exposed to any match outcome.

**2. Historical Pattern Store**
64 real price movement records from the 2014, 2018, and 2022 World Cups. Indexed by ticker and team for sub-millisecond retrieval during agent reasoning.

**3. Vector Search**
Every signal report is embedded using sentence-transformers (384 dimensions) and stored in Atlas Vector Search. Enables semantic retrieval — find past signals by meaning, not keywords.

---

## 🛠️ Tech Stack

- Agent: Google Gemini 2.5 Flash
- Database: MongoDB Atlas (vector search + document store)
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- Market Data: yfinance
- Backend: Python + Flask
- Frontend: Vanilla HTML/CSS/JS

---

## Running Locally

**1. Clone the repo**

git clone https://github.com/MadhavThankasala/sportsPulse.git
cd sportsPulse

**2. Install dependencies**

pip install pymongo yfinance flask google-genai sentence-transformers python-dotenv

**3. Set up environment variables**
Create a .env file:

MONGODB_URI=your_mongodb_atlas_connection_string
DB_NAME=sportspulse
GOOGLE_API_KEY=your_gemini_api_key

**4. Seed the database**

PYTHONPATH=. python data/seed_sponsors.py
PYTHONPATH=. python data/historical_patterns.py

**5. Run the app**

PYTHONPATH=. python app.py

Visit http://localhost:5000

---

## Project Structure

sportspulse/
├── agents/
│   └── signal_agent.py      # Gemini agent with tool definitions
├── data/
│   ├── seed_sponsors.py     # MongoDB knowledge graph seeding
│   └── historical_patterns.py # Historical price data ingestion
├── utils/
│   ├── db.py                # MongoDB connection
│   └── vector_search.py     # Embedding + semantic search
├── templates/
│   └── index.html           # Flask UI
└── app.py                   # Flask routes

---

## Roadmap

- Expand beyond World Cup — NFL, NBA, Olympics, F1
- Auto-detect match results via sports API
- Deploy to Google Cloud Run
- Add disclaimer and risk warnings for production

---

## Disclaimer

SportsPulse is a research and educational tool. It does not constitute financial advice. Always do your own research before making investment decisions.

---

Built for the Rapid Agent Hackathon (https://rapid-agent.devpost.com) · MongoDB Track