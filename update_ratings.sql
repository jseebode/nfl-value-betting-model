-- update_ratings.sql

-- 1. Helper Function: Calculate Win Probability
CREATE OR REPLACE FUNCTION get_expected_win_prob(rating_a NUMERIC, rating_b NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    RETURN 1.0 / (1.0 + POWER(10.0, (rating_b - rating_a) / 400.0));
END;
$$ LANGUAGE plpgsql;

-- 2. Main Procedure: Update Ratings with Time Decay and MOV
CREATE OR REPLACE PROCEDURE update_team_ratings()
LANGUAGE plpgsql
AS $$
DECLARE
    match_record RECORD;
    
    -- Constants
    K_BASE_FACTOR CONSTANT NUMERIC := 15.0;     -- Base K will be scaled up
    HFA CONSTANT NUMERIC := 65.0;              -- Home Field Advantage
    DECAY_RATE_PER_DAY CONSTANT NUMERIC := 0.003; -- Scales down K by 0.1% per day
    MIN_K_MULTIPLIER CONSTANT NUMERIC := 0.2;   -- Ensures old games still have at least 50% weight
    
    -- Variables
    home_rating NUMERIC;
    away_rating NUMERIC;
    game_count INT;
    
    latest_match_date DATE;
    days_old INT;
    time_decay_multiplier NUMERIC;
    
    expected_home_win_prob NUMERIC;
    score_diff NUMERIC;
    mov_multiplier NUMERIC;
    actual_score NUMERIC;
    
    dynamic_k_factor NUMERIC; -- New variable for the final calculated K
    new_home_rating NUMERIC;
    new_away_rating NUMERIC;
BEGIN
    RAISE NOTICE 'Starting team rating calculation with Time Decay and MOV...';
    
    -- Get the date of the most recent game loaded
    SELECT MAX(match_date) INTO latest_match_date FROM matches;
    
    -- 1. Reset ratings and get total game count
    UPDATE teams SET power_rating = 1500.00;
    SELECT count(*) INTO game_count FROM matches;
    
    -- 2. Loop through matches
    FOR match_record IN 
        SELECT match_id, match_date, home_team_id, away_team_id, home_score, away_score
        FROM matches
        WHERE home_score IS NOT NULL -- Only process completed games
        ORDER BY match_date ASC, match_id ASC -- Crucial: Must be chronological
    LOOP
        
        -- --- TIME DECAY CALCULATION ---
        -- Calculate how old the game is in days relative to the latest game
        days_old := latest_match_date - match_record.match_date;
        
        -- Multiplier linearly decays K from 1.0 (newest game) down to MIN_K_MULTIPLIER (oldest games)
        time_decay_multiplier := GREATEST(1.0 - (days_old * DECAY_RATE_PER_DAY), MIN_K_MULTIPLIER); 
        
        -- --- RATING UPDATE LOGIC ---
        
        -- Get current ratings
        SELECT power_rating INTO home_rating FROM teams WHERE team_id = match_record.home_team_id;
        SELECT power_rating INTO away_rating FROM teams WHERE team_id = match_record.away_team_id;

        -- Calculate Expected Probability (with HFA)
        expected_home_win_prob := get_expected_win_prob(home_rating + HFA, away_rating);
        score_diff := match_record.home_score - match_record.away_score;
        
        -- Determine Winner (1.0, 0.0, or 0.5)
        IF score_diff > 0 THEN actual_score := 1.0;
        ELSIF score_diff < 0 THEN actual_score := 0.0;
        ELSE actual_score := 0.5;
        END IF;
        
        -- Margin of Victory Multiplier
        mov_multiplier := LN(ABS(score_diff) + 1.0);
        
        -- Final K-Factor for this specific game
        dynamic_k_factor := K_BASE_FACTOR * mov_multiplier * time_decay_multiplier;
        
        -- Calculate New Ratings
        new_home_rating := home_rating + dynamic_k_factor * (actual_score - expected_home_win_prob);
        new_away_rating := away_rating + dynamic_k_factor * ((1.0 - actual_score) - (1.0 - expected_home_win_prob));
        
        -- Update Database
        UPDATE teams SET power_rating = new_home_rating WHERE team_id = match_record.home_team_id;
        UPDATE teams SET power_rating = new_away_rating WHERE team_id = match_record.away_team_id;
        
    END LOOP;
    
    RAISE NOTICE 'Calculation complete. Ratings updated for % games using MOV and Time Decay.', game_count;
END;
$$;