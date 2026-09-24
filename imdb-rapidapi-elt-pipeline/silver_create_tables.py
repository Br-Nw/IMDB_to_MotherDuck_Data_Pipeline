import duckdb
from dotenv import load_dotenv
import datetime

def create_silver_tables(motherduck_token):
    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:
        con.sql(''' 
        
        USE imdb_analytics;
        USE silver;

        BEGIN TRANSACTION;

            CREATE OR REPLACE TABLE directors (
            id INTEGER PRIMARY KEY,
            director VARCHAR UNIQUE
            );

            CREATE OR REPLACE TABLE certificates (
            id INTEGER PRIMARY KEY,
            certificate VARCHAR UNIQUE
            );

            CREATE OR REPLACE TABLE stars (
            id INTEGER PRIMARY KEY,
            star VARCHAR UNIQUE
            );

            CREATE OR REPLACE TABLE genres (
            id INTEGER PRIMARY KEY,
            genre VARCHAR UNIQUE    
            );

            CREATE OR REPLACE TABLE imdb_ranked_media (
            id INTEGER PRIMARY KEY, 
            rank INTEGER,
            title VARCHAR,
            released_year INTEGER,
            poster_link VARCHAR,
            certificate_id INTEGER,
            runtime_minutes INTEGER,
            imdb_rating DECIMAL(2, 1),
            overview VARCHAR,
            meta_score INTEGER,
            director_id INTEGER,
            no_of_votes INTEGER,
            gross_revenue_usd INTEGER,

            FOREIGN KEY (certificate_id) REFERENCES certificates(id),
            FOREIGN KEY (director_id) REFERENCES directors(id)
            );

            CREATE OR REPLACE TABLE media_stars (
            media_id INTEGER,
            star_id INTEGER,

            PRIMARY KEY (media_id, star_id),
            FOREIGN KEY (media_id) REFERENCES imdb_ranked_media(id),
            FOREIGN KEY (star_id) REFERENCES stars(id)
            );

            CREATE OR REPLACE TABLE media_genres (
            media_id INTEGER,
            genre_id INTEGER,

            PRIMARY KEY (media_id, genre_id),
            FOREIGN KEY (media_id) REFERENCES imdb_ranked_media(id),
            FOREIGN KEY (genre_id) REFERENCES genres(id)
            );

        COMMIT;
        ''')

        timestamp = datetime.datetime.now(datetime.timezone.utc)
        # Records the time at which the data was successfully loaded.
        # Timestamp is in UTC.

        return  (
                f"\n===| ALL SILVER LAYER TABLES CREATED AT {timestamp} UTC |===\n\n"
                )