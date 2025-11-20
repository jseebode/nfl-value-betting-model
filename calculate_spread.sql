-- calculate_spread.sql

CREATE OR REPLACE FUNCTION calculate_predicted_spread(
    home_team_abbr VARCHAR, 
    away_team_abbr VARCHAR
)
RETURNS NUMERIC AS $$
DECLARE
    home_rating NUMERIC;
    away_rating NUMERIC;
    HFA CONSTANT NUMERIC := 65.0; -- The same Home Field Advantage value used in modeling
    predicted_spread NUMERIC;
BEGIN
    -- Get current power ratings from the teams table
    SELECT power_rating INTO home_rating 
    FROM teams 
    WHERE abbreviation = home_team_abbr;

    SELECT power_rating INTO away_rating 
    FROM teams 
    WHERE abbreviation = away_team_abbr;

    -- Calculate Predicted Spread: (Home Rating - Away Rating) / 10 * K
    -- Note: Elo difference is often scaled down to points. We use a simple 10-point scaling factor.
    predicted_spread := (away_rating - home_rating - HFA) / 10.0;
    
    RETURN predicted_spread;
END;
$$ LANGUAGE plpgsql;