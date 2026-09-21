# RUN PIPELINE SCRIPT

from dotenv import load_dotenv
import os
load_dotenv()
from bronze_ingestion import load_imdb_data#

# CONFIGURATION
# --------------------------------------------------------------------
x_rapidapi_key = os.getenv("X-RAPIDAPI-KEY")
motherduck_token = os.getenv("MOTHERDUCKTOKEN")
# The .env file contains sensitive credentials such as the
# RapidAPI key and MotherDuck access token.

# STEP 1: INGEST DATA INTO BRONZE LAYER
# --------------------------------------------------------------------
print(load_imdb_data(x_rapidapi_key, motherduck_token))