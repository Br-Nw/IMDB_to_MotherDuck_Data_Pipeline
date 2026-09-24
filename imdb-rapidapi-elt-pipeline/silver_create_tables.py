import duckdb
from dotenv import load_dotenv
import datetime

def create_silver_tables(motherduck_token):
    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:
        con.sql(''' 

            USE imdb_analytics;
            USE silver;

            BEGIN TRANSACTION;

                DROP TABLE IF EXISTS media_genres;
                DROP TABLE IF EXISTS media_stars;
                DROP TABLE IF EXISTS imdb_ranked_media;
                DROP TABLE IF EXISTS genres;
                DROP TABLE IF EXISTS stars;
                DROP TABLE IF EXISTS certificates;
                DROP TABLE IF EXISTS directors;

                DROP SEQUENCE IF EXISTS genre_id_seq;
                DROP SEQUENCE IF EXISTS star_id_seq;
                DROP SEQUENCE IF EXISTS certificate_id_seq;
                DROP SEQUENCE IF EXISTS director_id_seq;
                
                CREATE SEQUENCE director_id_seq START 1;

                CREATE TABLE directors (
                id INTEGER DEFAULT nextval('director_id_seq') PRIMARY KEY,
                director VARCHAR UNIQUE
                );

                CREATE SEQUENCE certificate_id_seq START 1;

                CREATE TABLE certificates (
                id INTEGER DEFAULT nextval('certificate_id_seq') PRIMARY KEY,
                certificate VARCHAR UNIQUE
                );

                CREATE SEQUENCE star_id_seq START 1;

                CREATE TABLE stars (
                id INTEGER DEFAULT nextval('star_id_seq') PRIMARY KEY,
                star VARCHAR UNIQUE
                );

                CREATE SEQUENCE genre_id_seq START 1;

                CREATE TABLE genres (
                id INTEGER DEFAULT nextval('genre_id_seq') PRIMARY KEY,
                genre VARCHAR UNIQUE    
                );

                CREATE TABLE imdb_ranked_media (
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

                CREATE TABLE media_stars (
                media_id INTEGER,
                star_id INTEGER,

                PRIMARY KEY (media_id, star_id),
                FOREIGN KEY (media_id) REFERENCES imdb_ranked_media(id),
                FOREIGN KEY (star_id) REFERENCES stars(id)
                );

                CREATE TABLE media_genres (
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

        return (f"\n===| ALL SILVER LAYER TABLES CREATED AT {timestamp} UTC |===\n")
        # Returns a simple pipeline status message indicating that all silver layer tables have been created.