import requests
import pandas as pd
import datetime
import duckdb


def load_imdb_data(x_rapidapi_key, motherduck_token):

        # API HTTP REQUEST CONFIGURATION
        # --------------------------------------------------------------------
        
        url = "https://imdb-top-1000-movies-series.p.rapidapi.com/byrating"
        # Defines the RapidAPI endpoint used to retrieve the IMDb movie data.

        headers = {
                "x-rapidapi-key": x_rapidapi_key,
                "x-rapidapi-host": "imdb-top-1000-movies-series.p.rapidapi.com",
                "Content-Type": "application/x-www-form-urlencoded"
        }
        # HTTP request headers.
        # The API key authenticates the request, while the host identifies
        # the RapidAPI service being accessed.


        payload = {
                "above": "1",
                "under": "11"
        }
        # Parameters sent to the API.
        # Requests the full available IMDb rating range.


        # API DATA EXTRACTION
        # --------------------------------------------------------------------

        response = requests.post(
                url,
                data=payload,
                headers=headers
        ) # Sends a HTTP POST request to the IMDb API.

        response.raise_for_status() # Raises an exception if the API returns an unsuccessful HTTP status code.

        raw_movie_df = pd.DataFrame.from_dict(response.json())

        # Converts the API JSON response into a Pandas DataFrame
        # for loading into the Bronze layer.

        # MOTHERDUCK LOAD
        # --------------------------------------------------------------------
    
        with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con: 

                con.sql('''
                BEGIN TRANSACTION;

                        CREATE DATABASE IF NOT EXISTS imdb_analytics;

                        CREATE SCHEMA IF NOT EXISTS imdb_analytics.bronze;
                        CREATE SCHEMA IF NOT EXISTS imdb_analytics.silver;
                        CREATE SCHEMA IF NOT EXISTS imdb_analytics.gold;
                        
                        USE imdb_analytics;
                        USE bronze;

                        CREATE OR REPLACE TABLE raw_movie_data AS
                        SELECT * FROM raw_movie_df; 

                COMMIT; 
                ''')

                # Creates imdb_analytics database if it does not already exist.

                # Creates the three layers of the medallion architecture.
                # Bronze = raw data
                # Silver = cleaned/transformed data
                # Gold   = analytics-ready data

                # Then creates or replaces the raw movie table in the Bronze layer.

                # INGESTION METADATA
                # --------------------------------------------------------------------
                con.sql('''

                USE imdb_analytics;
                USE bronze;

                BEGIN TRANSACTION;
                
                        CREATE SEQUENCE IF NOT EXISTS ingestion_id_seq START 1;

                        CREATE TABLE IF NOT EXISTS ingestion_metadata (
                                load_id INTEGER DEFAULT nextval('ingestion_id_seq') PRIMARY KEY,
                                source VARCHAR,
                                loaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                                row_count INTEGER
                        );

                        INSERT INTO ingestion_metadata (source, row_count)
                        VALUES 
                        (
                        'IMDb RapidAPI',
                        (SELECT COUNT(*) FROM raw_movie_data)
                        );
                
                COMMIT;
                ''')
                # Creates a table containing metadata about the ingested movie data,
                # including the data source, ingestion timestamp, and number of rows loaded.
                
                timestamp = datetime.datetime.now(datetime.timezone.utc)
                # Records the time at which the data was successfully loaded.
                # Timestamp is in UTC.

        return (
                f"\n===| HTTP STATUS CODE: {response.status_code} |===\n\n"
                f"===| DATABASE, MEDALLION SCHEMA AND MOVIE DATA "
                f"LOADED INTO BRONZE LAYER AT {timestamp} UTC |==="
        )
        # Returns a simple pipeline status message showing that the API request
        # succeeded and the data was loaded into the Bronze layer.