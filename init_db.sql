-- init_db.sql

-- 1. Teams Table: Stores core info and your calculated Power Rating (ELO/DVOA equivalent)
CREATE TABLE IF NOT EXISTS teams (
    team_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    abbreviation VARCHAR(5) UNIQUE NOT NULL,
    -- This column holds the rating that your PL/pgSQL function will update
    power_rating NUMERIC(10, 2) DEFAULT 1500.00, 
    -- Other calculated metrics from nfl-data-py can go here later
    off_ppg NUMERIC(5, 2) DEFAULT 0.00,
    def_ppg NUMERIC(5, 2) DEFAULT 0.00
);

-- 2. Matches Table: Stores historical results and live betting odds
CREATE TABLE IF NOT EXISTS matches (
    match_id SERIAL PRIMARY KEY,
    match_date DATE NOT NULL,
    home_team_id INT REFERENCES teams(team_id),
    away_team_id INT REFERENCES teams(team_id),
    
    -- Historical Results (for modeling/training)
    home_score INT,
    away_score INT,
    
    -- Live Odds (from external API)
    market_spread NUMERIC(4, 1),      -- e.g., -7.5, +3.0
    market_total NUMERIC(4, 1)        -- e.g., 48.5
);

-- 3. Value Picks Table: Stores the output of your predictive model
CREATE TABLE IF NOT EXISTS value_picks (
    pick_id SERIAL PRIMARY KEY,
    match_id INT REFERENCES matches(match_id) UNIQUE, -- Only one prediction per match
    
    -- Your Model's Predictions
    predicted_spread NUMERIC(4, 1),
    predicted_total NUMERIC(4, 1),
    
    -- Value Calculations
    spread_value_score NUMERIC(5, 3), -- Positive score means value
    total_value_score NUMERIC(5, 3),
    
    -- Time stamp to know when the pick was generated
    generated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);