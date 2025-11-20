# NFL Value Betting Model 🏈💰

A full-stack NFL betting-edge detector that pulls live odds, calculates custom power ratings, and returns +EV picks via a REST API.


Features

Live odds ingestion from TheOddsAPI
Custom Elo-style power ratings with:
Margin-of-Victory multiplier
Time-decay weighting (recent games matter more)

PL/pgSQL prediction function in PostgreSQL
Flask REST API with real-time value picks endpoint
Fully Dockerized (Flask + PostgreSQL) – docker-compose up and it’s running

Tech Stack

Python 3.11
Flask
PostgreSQL + PL/pgSQL
Docker Compose
Pandas
nfl_data_py
requests

Quick Start
Bash# 1. Clone and enter repo
git clone https://github.com/yourusername/nfl-value-betting-model.git
cd nfl-value-betting-model

# 2. Start everything (Postgres + Flask)
docker-compose up --build

# 3. Load data (run these inside the Flask container or from host)
docker exec -it nfl_flask_app python insert_teams.py
docker exec -it nfl_flask_app python load_historical_data.py
docker exec -it nfl_flask_app python load_odds.py   # needs your TheOddsAPI key

# 4. Get live value picks
curl http://localhost:5000/api/v1/value_picks
