import os
import psycopg2
import time

# List of the 32 NFL teams (Abbreviation, Full Name)
NFL_TEAMS = [
    ('ARI', 'Arizona Cardinals'), ('ATL', 'Atlanta Falcons'), ('BAL', 'Baltimore Ravens'),
    ('BUF', 'Buffalo Bills'), ('CAR', 'Carolina Panthers'), ('CHI', 'Chicago Bears'),
    ('CIN', 'Cincinnati Bengals'), ('CLE', 'Cleveland Browns'), ('DAL', 'Dallas Cowboys'),
    ('DEN', 'Denver Broncos'), ('DET', 'Detroit Lions'), ('GB', 'Green Bay Packers'),
    ('HOU', 'Houston Texans'), ('IND', 'Indianapolis Colts'), ('JAX', 'Jacksonville Jaguars'),
    ('KC', 'Kansas City Chiefs'), ('LAC', 'Los Angeles Chargers'), ('LAR', 'Los Angeles Rams'),
    ('LV', 'Las Vegas Raiders'), ('MIA', 'Miami Dolphins'), ('MIN', 'Minnesota Vikings'),
    ('NE', 'New England Patriots'), ('NO', 'New Orleans Saints'), ('NYG', 'New York Giants'),
    ('NYJ', 'New York Jets'), ('PHI', 'Philadelphia Eagles'), ('PIT', 'Pittsburgh Steelers'),
    ('SF', 'San Francisco 49ers'), ('SEA', 'Seattle Seahawks'), ('TB', 'Tampa Bay Buccaneers'),
    ('TEN', 'Tennessee Titans'), ('WAS', 'Washington Commanders')
]

# Database connection details (matching docker-compose.yml)
DB_URL = "postgresql://postgres:postgres_password@postgres_db:5432/nfl_db"
# NOTE: Using 'localhost' here because we are running the script *outside* the container

def insert_teams():
    conn = None
    try:
        # Establish connection
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # SQL Insert statement using ON CONFLICT to prevent errors if run twice
        sql = """INSERT INTO teams (abbreviation, name) 
                 VALUES (%s, %s) 
                 ON CONFLICT (abbreviation) DO NOTHING;"""
        
        print("Inserting 32 NFL teams...")
        
        # Execute the SQL for every team
        for team in NFL_TEAMS:
            cur.execute(sql, team)
        
        # Commit the transaction to save the changes
        conn.commit()
        cur.close()
        print("✅ Team insertion complete!")

    except psycopg2.Error as e:
        print(f"Database error occurred: {e}")
    finally:
        if conn is not None:
            conn.close()
            
if __name__ == "__main__":
    # Wait a moment to ensure the database is fully ready
    time.sleep(2) 
    insert_teams()