# RUN PIPELINE SCRIPT

from dotenv import load_dotenv
import os
import datetime
from bronze_ingestion import load_imdb_data
from silver_create_tables import create_silver_tables
from silver_load_into_tables import load_silver_lookup_tables, load_silver_fact_table, load_silver_bridge_tables
from gold_load_into_flat_mart import load_gold_flat_mart
from gold_load_director_tables import load_gold_director_tables
from gold_load_into_genre_metrics_table import load_gold_genre_metrics_table

# CONFIGURATION
# --------------------------------------------------------------------
load_dotenv()
x_rapidapi_key = os.getenv("X-RAPIDAPI-KEY")
motherduck_token = os.getenv("MOTHERDUCKTOKEN")
# The .env file contains sensitive credentials such as the
# RapidAPI key and MotherDuck access token.

# STEP 1: INGEST DATA INTO BRONZE LAYER
# --------------------------------------------------------------------
print(load_imdb_data(x_rapidapi_key, motherduck_token))

# STEP 2: CREATE TABLES IN SILVER LAYER
# --------------------------------------------------------------------
print(create_silver_tables(motherduck_token))

# STEP 3: LOAD DATA INTO SILVER LAYER TABLES
# --------------------------------------------------------------------
print(load_silver_lookup_tables(motherduck_token))
print(load_silver_fact_table(motherduck_token))
print(load_silver_bridge_tables(motherduck_token))

# STEP 4: LOAD DATA INTO GOLD LAYER TABLES
# --------------------------------------------------------------------
print(load_gold_flat_mart(motherduck_token))
print(load_gold_director_tables(motherduck_token))
print(load_gold_genre_metrics_table(motherduck_token))

# STEP 5: ALL DATA LOADED INTO MOTHERDUCK
# --------------------------------------------------------------------

end_timestamp = datetime.datetime.now(datetime.timezone.utc)
# Records the time at which the data was successfully loaded.
# Timestamp is in UTC.

print(f"\n===|||| PIPELINE SUCCESS: ALL IMDB TOP 1000 (MOVIES, SERIES) DATA LOADED INTO MOTHERDUCK AT {end_timestamp} UTC ||||===\n")