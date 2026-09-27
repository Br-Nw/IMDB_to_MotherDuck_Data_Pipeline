import duckdb
import pandas as pd
import datetime

def load_gold_flat_mart(motherduck_token):

    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:
        
        con.sql("""
                USE imdb_analytics;
                USE gold;

                BEGIN TRANSACTION;
            """)

        con.sql(""" 

            CREATE OR REPLACE TABLE media_flat_mart AS

                WITH media_flat_table AS (

                    WITH media_flat AS (
                        
                        SELECT
                        
                        silver.imdb_ranked_media.id,
                        rank,
                        title,
                        released_year,
                        poster_link,
                        certificates.certificate,
                        runtime_minutes,
                        media_genres.genre_id, -- POINT OF INTREST FOR genres table JOIN
                        imdb_rating,
                        overview,
                        meta_score,
                        directors.director,
                        media_stars.star_id, -- POINT OF INTREST FOR stars table JOIN
                        no_of_votes,
                        gross_revenue_usd,
                        MEDIAN(gross_revenue_usd) OVER() AS median_gross_revenue_usd,
                        
                        CASE
                        WHEN gross_revenue_usd IS NOT NULL
                        THEN TRUE
                        
                        WHEN gross_revenue_usd IS NULL
                        THEN FALSE
                        END AS gross_given
                        
                        FROM silver.imdb_ranked_media
                        
                        LEFT JOIN silver.certificates
                        ON imdb_ranked_media.certificate_id = certificates.id
                        
                        LEFT JOIN silver.media_genres
                        ON imdb_ranked_media.id = media_genres.media_id
                        
                        LEFT JOIN silver.media_stars
                        ON imdb_ranked_media.id = media_stars.media_id
                        
                        LEFT JOIN silver.directors
                        ON imdb_ranked_media.director_id = directors.id
                        )
                        
                    SELECT 
                        id,
                        rank,
                        title,
                        released_year,
                        poster_link,
                        certificate,
                        runtime_minutes,
                        genre_id, -- POINT OF INTREST FOR genres table JOIN
                        imdb_rating,
                        overview,
                        meta_score,
                        director,
                        star_id, -- POINT OF INTREST FOR stars table JOIN
                        no_of_votes,
                        gross_revenue_usd,
                        median_gross_revenue_usd,
                        gross_given
                    
                    FROM media_flat
                    ORDER BY id ASC
                    ) 

                    SELECT 

                    media_flat_table.id,
                    rank,
                    title,
                    released_year,
                    poster_link,
                    certificate,
                    runtime_minutes,
                    genre, 
                    imdb_rating,
                    overview,
                    meta_score,
                    director,
                    star, 
                    no_of_votes,
                    gross_revenue_usd,
                    median_gross_revenue_usd,
                    gross_given
                    
                    FROM media_flat_table

                    LEFT JOIN silver.genres
                    ON media_flat_table.genre_id = genres.id

                    LEFT JOIN silver.stars
                    ON media_flat_table.star_id = stars.id

            """)
        
        con.sql("""COMMIT;""")

        # Creates a flattened media table by joining IMDb movies with certificates, genres, stars, and directors,
        # while also calculating the median gross revenue and indicating whether gross revenue is available.
        # The final result replaces genre/star IDs with their names for easier analysis and reporting.
        # This table is completely denormalised and contains some repeating values for fast analytical queries.  


        timestamp = datetime.datetime.now(datetime.timezone.utc)
        # Records the time at which the data was successfully loaded.
        # Timestamp is in UTC.
        
        return (f"===| MEDIA FLAT MART LOADED INTO GOLD LAYER AT {timestamp} UTC |===\n")