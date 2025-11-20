import pandas as pd
import nfl_data_py as nfl
import psycopg2
import os

Python# Fix inconsistent abbreviations from nfl_data_py
ABBR_FIX = {
    'JAC': 'JAX',
    'LAR': 'LA', 
    'LVR': 'LV',
    'WAS': 'WSH',
    'LA': 'LAR',
    'LV': 'LVR'
}

# Inside load_historical_data(), after df = nfl.import_schedules(...)
df['home_team'] = df['home_team'].replace(ABBR_FIX)
df['away_team'] = df['away_team'].replace(ABBR_FIX)
# Database connection details (must match service name for container access)
DB_URL = "postgresql://postgres:postgres_password@postgres_db:5432/nfl_db"

def get_team_id_map(conn):
    """Fetches team abbreviations and IDs from the DB."""
    sql = "SELECT team_id, abbreviation FROM teams;"
    with conn.cursor() as cur:
        cur.execute(sql)
        # Creates a mapping: {'ARI': 1, 'BAL': 2, ...}
        return {abbr: id for id, abbr in cur.fetchall()}

def load_historical_data():
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        team_id_map = get_team_id_map(conn)
        
        # 1. Extract: Fetch data for the last three seasons (2022-2024)
        print("1. Extracting 3 seasons of historical NFL data...")
        df = nfl.import_schedules([2024,2025])
        
        # 2. Transform: Filter, clean, and map data
        df = df[df['game_type'] == 'REG'] # Only regular season games
        df = df[['gameday', 'home_team', 'away_team', 'home_score', 'away_score']].copy()
        df = df.dropna(subset=['home_score', 'away_score'])
        df['home_team_id'] = df['home_team'].map(team_id_map)
        df['away_team_id'] = df['away_team'].map(team_id_map)

        df = df.dropna(subset=['home_team_id', 'away_team_id'])
        # ... (rest of the code)

        # Select only the columns needed for the final insert
        # *** CHANGE 'game_date' to 'gameday' HERE ***
        df_insert = df[['gameday', 'home_team_id', 'away_team_id', 'home_score', 'away_score']]
        
        # 3. Load: Prepare SQL INSERT statement
        sql = """INSERT INTO matches (match_date, home_team_id, away_team_id, home_score, away_score) 
                 VALUES (%s, %s, %s, %s, %s)
                 ON CONFLICT DO NOTHING;"""
        
        with conn.cursor() as cur:
            print("2. Transforming and Loading matches into the database...")
            
            # Loop through the rows and execute the insert
            for index, row in df_insert.iterrows():
                # Data is inserted as a tuple, which psycopg2 handles
                data = (row['gameday'], row['home_team_id'], row['away_team_id'], 
                        row['home_score'], row['away_score'])           
                cur.execute(sql, data)

            conn.commit()
            print(f"✅ Loaded {len(df_insert)} historical matches successfully!")

    except psycopg2.Error as e:
        print(f"Database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    load_historical_data()