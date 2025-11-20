import os
import psycopg2
from flask import Flask, jsonify
from datetime import date

app = Flask(__name__)

DB_URL = "postgresql://postgres:postgres_password@postgres_db:5432/nfl_db"

def get_db_connection():
    return psycopg2.connect(DB_URL)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "NFL Value Betting API is Running!", "status": "Ready"})

@app.route('/api/v1/value_picks', methods=['GET'])
def get_value_picks():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        sql_query = """
            SELECT
                m.match_date,
                t_home.abbreviation AS home_team,
                t_away.abbreviation AS away_team,
                m.market_spread,
                calculate_predicted_spread(t_home.abbreviation, t_away.abbreviation) AS predicted_spread,
                ABS(calculate_predicted_spread(t_home.abbreviation, t_away.abbreviation) - m.market_spread) AS value_score
            FROM matches m
            JOIN teams t_home ON m.home_team_id = t_home.team_id
            JOIN teams t_away ON m.away_team_id = t_away.team_id
            WHERE m.market_spread IS NOT NULL 
              AND m.match_date >= CURRENT_DATE 
              AND m.home_score IS NULL
              AND ABS(calculate_predicted_spread(t_home.abbreviation, t_away.abbreviation) - m.market_spread) > 3.0
            ORDER BY value_score DESC;
        """
        
        cur.execute(sql_query)
        results = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        
        picks = []
        for row in results:
            pick = dict(zip(columns, row))
            if isinstance(pick.get('match_date'), date):
                pick['match_date'] = pick['match_date'].isoformat()

            predicted = pick['predicted_spread'] or 0
            market = pick['market_spread'] or 0
            edge = predicted - market  # Positive = model likes away team more

            if edge > 3:
                pick['recommended_bet'] = f"{pick['away_team']} +{abs(market):.1f}"
                pick['edge_reason'] = f"Model favors away team by {edge:.1f} points"
            elif edge < -3:
                pick['recommended_bet'] = f"{pick['home_team']} {market:.1f}"
                pick['edge_reason'] = f"Model favors home team by {abs(edge):.1f} points"
            else:
                pick['recommended_bet'] = "No strong edge"
                pick['edge_reason'] = "Within 3-point margin"

            picks.append(pick)

        return jsonify(picks), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve value picks", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)