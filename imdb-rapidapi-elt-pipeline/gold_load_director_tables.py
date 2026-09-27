import duckdb
import pandas as pd
import datetime

def load_gold_director_tables(motherduck_token):

    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:
        
        con.sql("""
                USE imdb_analytics;
                USE gold;

                BEGIN TRANSACTION;
            """)
        
    # -- CREATES DIRECTORS DIMENSION TABLE --
        con.sql(""" 
       
            CREATE OR REPLACE TABLE directors (
                id INTEGER PRIMARY KEY,
                director VARCHAR
            );

            INSERT INTO directors (
                id,
                director
            )
            SELECT
                id,
                director
            FROM silver.directors;

            """)

    # -- CREATES DIRECTOR METRICS TABLE --
        con.sql("""
        
        CREATE OR REPLACE TABLE director_metrics (
            director_id INTEGER PRIMARY KEY,
            mean_gross_revenue_usd INTEGER,
            mean_imdb_rating DECIMAL(2, 1),
            mean_meta_score INTEGER,
            
            FOREIGN KEY (director_id) REFERENCES directors(id)
        );

        INSERT INTO director_metrics (
            director_id,
            mean_gross_revenue_usd,
            mean_imdb_rating,
            mean_meta_score
        )
        SELECT

            director_id,
            CAST(AVG(gross_revenue_usd) AS INTEGER) AS mean_gross_revenue_usd,
            CAST(AVG(imdb_rating) AS DECIMAL(2, 1)) AS mean_imdb_rating,
            CAST(AVG(meta_score) AS INTEGER) AS mean_meta_score

        FROM silver.imdb_ranked_media
        GROUP BY director_id
        ORDER BY mean_imdb_rating DESC, mean_gross_revenue_usd DESC;

        """)
        
        con.sql("""COMMIT;""")

        # The code above creates director dimension and metrics tables by loading director data from Silver
        # and calculating average gross revenue, IMDb rating, and Meta Score for each director.

        timestamp = datetime.datetime.now(datetime.timezone.utc)
        # Records the time at which the data was successfully loaded.
        # Timestamp is in UTC.
        
        return (f"===| DIRECTORS LOOK UP TABLE AND DIRECTOR METRICS TABLE LOADED INTO GOLD LAYER AT {timestamp} UTC |===\n")