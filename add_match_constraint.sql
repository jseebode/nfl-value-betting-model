ALTER TABLE matches 
ADD CONSTRAINT unique_match_date_teams 
UNIQUE (match_date, home_team_id, away_team_id);