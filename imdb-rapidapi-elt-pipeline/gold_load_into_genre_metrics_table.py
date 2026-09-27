import duckdb
import pandas as pd
import datetime

def load_gold_genre_metrics_table(motherduck_token):

    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:
        
        con.sql("""
                USE imdb_analytics;
                USE gold;

                BEGIN TRANSACTION;
            """)
        
        con.sql(""" 

        DROP TABLE IF EXISTS genre_metrics;

        CREATE TABLE genre_metrics (
            genre_id INTEGER PRIMARY KEY,
            genre VARCHAR,
            mean_runtime_minutes INTEGER,
            total_gross_revenue_usd BIGINT,
            median_imdb_rating DECIMAL(2,1),
            median_meta_score INTEGER,
            total_votes BIGINT,
            genre_count_in_dataset INTEGER 
            );

            """)

        con.sql(""" 
        

        INSERT INTO genre_metrics (
            genre_id,
            genre,
            mean_runtime_minutes,
            total_gross_revenue_usd,
            median_imdb_rating,
            median_meta_score,
            total_votes,
            genre_count_in_dataset
        )
        WITH media_flat_table AS (
            
        WITH media_flat AS (
            
        SELECT
            
            runtime_minutes,
            media_genres.genre_id, -- POINT OF INTREST FOR genres table JOIN
            imdb_rating,
            meta_score,
            no_of_votes,
            gross_revenue_usd
            
            FROM silver.imdb_ranked_media
            
            LEFT JOIN silver.media_genres
            ON imdb_ranked_media.id = media_genres.media_id
            )
            
        SELECT 

            runtime_minutes,
            genre_id, -- POINT OF INTREST FOR genres table JOIN
            imdb_rating,
            meta_score,
            no_of_votes,
            gross_revenue_usd
        
        FROM media_flat
        ) 

        SELECT

            genre_id,
            genre,
            CAST(AVG(runtime_minutes) AS INTEGER) AS mean_runtime_minutes,
            CAST(SUM(gross_revenue_usd) AS BIGINT) AS total_gross_revenue_usd,
            CAST(MEDIAN(imdb_rating) AS DECIMAL(2,1)) AS median_imdb_rating,
            CAST(MEDIAN(meta_score) AS INTEGER) AS median_meta_score, 
            CAST(SUM(no_of_votes) AS BIGINT) AS total_votes,
            COUNT(genre) AS genre_count_in_dataset
        
        FROM media_flat_table

        LEFT JOIN silver.genres
        ON media_flat_table.genre_id = genres.id

        GROUP BY genre_id, genre
        ORDER BY genre_id;
        
        """)
                
        con.sql("""COMMIT;""")

        # The code above creates the genre metrics table by loading genre data from the Silver layer
        # and calculating average runtime, total gross revenue, median IMDb rating, median meta score,
        # total votes, and the number of movies for each genre.

        timestamp = datetime.datetime.now(datetime.timezone.utc)
        # Records the time at which the data was successfully loaded.
        # Timestamp is in UTC.
        
        return (f"===| GENRE METRICS TABLE LOADED INTO GOLD LAYER AT {timestamp} UTC |===\n")