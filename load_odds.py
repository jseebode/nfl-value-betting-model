import requests
import psycopg2
import os
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = '11ec5a39eba11c184f8b781cb8a701d2'  # <<< REPLACE THIS with your actual API key
SPORT_KEY = 'americanfootball_nfl'
REGIONS = 'us'
MARKETS = 'spreads,totals' # We focus on Spreads and Totals
ODDS_FORMAT = 'decimal'
# ---------------------

DB_URL = "postgresql://postgres:postgres_password@postgres_db:5432/nfl_db"

FULL_NAME_TO_ABBR = {
    'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF', 'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX',
    'Kansas City Chiefs': 'KC', 'Los Angeles Chargers': 'LAC', 'Los Angeles Rams': 'LAR',
    'Las Vegas Raiders': 'LV', 'Miami Dolphins': 'MIA', 'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
    'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT',
    'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS'
}

def get_team_id_map(conn):
    """Fetches team abbreviations and IDs from the DB."""
    sql = "SELECT team_id, abbreviation FROM teams;"
    with conn.cursor() as cur:
        cur.execute(sql)
        # Creates a mapping: {'ARI': 1, 'BAL': 2, ...}
        return {name: id for id, name in cur.fetchall()}

def get_live_odds():
    """Fetches upcoming NFL game odds from The Odds API."""
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds'
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': ODDS_FORMAT,
        'dateFormat': 'iso', # Use ISO format for date/time
    }
    
    print("1. Fetching live NFL odds...")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds: {e}")
        return None

def update_db_with_odds(odds_data):
    """Parses odds data and updates the matches table."""
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        team_id_map = get_team_id_map(conn)
        cur = conn.cursor()
        
        print("2. Parsing odds and updating database...")
        update_count = 0
        for game in odds_data:
            home_team = game['home_team']
            away_team = game['away_team']
            commence_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
            
            # Map team names to abbreviations (NFL abbreviations are standard)
            home_abbr = FULL_NAME_TO_ABBR.get(home_team)
            away_abbr = FULL_NAME_TO_ABBR.get(away_team)
            
            home_id = team_id_map.get(home_abbr)
            away_id = team_id_map.get(away_abbr)
            
            if not home_id or not away_id:
                # Skip games where team names couldn't be mapped to your internal IDs
                continue 

            # Find Spread and Total odds from bookmakers
            market_spread = None
            market_total = None
    
            # Simple logic: Find the best spread and total across all bookmakers
            # Inside the bookmaker loop, replace the spread section with:
            for bookmaker in game['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == 'spreads' and market_spread is None:
                        for outcome in market['outcomes']:
                            if outcome['name'] == home_team:
                                market_spread = outcome['point']  # Home perspective
                                break
                        break  # Only need first bookmaker with spread
            
            # SQL: UPSERT (UPDATE or INSERT) the upcoming match with the market odds
            sql_upsert = """
                INSERT INTO matches (match_date, home_team_id, away_team_id, market_spread, market_total)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (match_date, home_team_id, away_team_id)
                DO UPDATE SET
                    market_spread = EXCLUDED.market_spread,
                    market_total = EXCLUDED.market_total;
            """
            
            cur.execute(sql_upsert, (commence_time.date(), home_id, away_id, market_spread, market_total))
            update_count += 1
            
        conn.commit()
        print(f"✅ Successfully updated {update_count} upcoming matches with live odds.")

    except psycopg2.Error as e:
        print(f"Database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    odds_data = get_live_odds()
    if odds_data:
        update_db_with_odds(odds_data)