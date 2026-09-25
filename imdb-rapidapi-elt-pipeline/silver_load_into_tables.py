import duckdb
import pandas as pd
import datetime


def load_silver_lookup_tables(motherduck_token):

    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:
        raw_ranked_media_df = con.sql("SELECT * FROM imdb_analytics.bronze.raw_ranked_media_data;").df() # Nested bronze data loaded as a DataFrame

    df = pd.DataFrame.from_dict(list(raw_ranked_media_df["result"])) # Extracted Dataframe from nested JSON DataFrame

    # Transforms nested string list (example: 'Crime, Drama' --> 'Crime', 'Drama')
    def unnest_string(series):
        nested_string_list = list(series.dropna().drop_duplicates())
        unnested_string_list = []
        for val in nested_string_list:
            val_list = val.split(', ')
            for item in val_list:
                unnested_string_list.append(item)
        return pd.Series(unnested_string_list).drop_duplicates().to_frame(name="genre")

    # Transform stars data
    combine_stars = list(df["Star1"].dropna().drop_duplicates()) + list(df["Star2"].dropna().drop_duplicates()) + list(df["Star3"].dropna().drop_duplicates()) + list(df["Star4"].dropna().drop_duplicates())
    star_series = pd.Series(combine_stars)

    # DataFrames containing unique values for ranked_media lookup tables.
    stars_load_df = star_series.drop_duplicates().to_frame(name="star")
    certs_load_df = df["Certificate"].dropna().drop_duplicates().to_frame(name="certificate")
    directors_load_df = df["Director"].dropna().drop_duplicates().to_frame(name="director")
    genre_load_df = unnest_string(df["Genre"])

    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:
        
        con.sql("""
            USE imdb_analytics;
            USE silver;
            BEGIN TRANSACTION;
        """)

        # THIS CODE LOADS DATA INTO DIRECTORS TABLE
        con.register("directors_data", directors_load_df)

        con.sql("""
            INSERT INTO directors(director)
            SELECT director
            FROM directors_data;
        """)
        # ===========================================

        # THIS CODE LOADS DATA INTO STARS TABLE
        con.register("stars_data", stars_load_df)

        con.sql("""
            INSERT INTO stars(star)
            SELECT star
            FROM stars_data;
        """)
        # ===========================================

        # THIS CODE LOADS DATA INTO CERTIFICATES TABLE
        con.register("certificate_data", certs_load_df)

        con.sql("""
            INSERT INTO certificates(certificate)
            SELECT certificate
            FROM certificate_data;
        """)
        # ===========================================

        # THIS CODE LOADS DATA INTO GENRES TABLE
        con.register("genre_data", genre_load_df )

        con.sql("""
            INSERT INTO genres(genre)
            SELECT genre
            FROM genre_data;
        """)
        # ===========================================

        con.sql("COMMIT;")

    timestamp = datetime.datetime.now(datetime.timezone.utc)
    # Records the time at which the data was successfully loaded.
    # Timestamp is in UTC.

    return (f"===| DIRECTORS, STARS, CERTIFICATES, AND GENRES DATA LOADED INTO SILVER LAYER AT {timestamp} UTC |===\n")



def load_silver_fact_table(motherduck_token):

    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:

        raw_ranked_media_df = con.sql("SELECT * FROM imdb_analytics.bronze.raw_ranked_media_data;").df() # Nested bronze data loaded as a DataFrame from motherduck

        media_df = pd.DataFrame.from_dict(list(raw_ranked_media_df["result"])) # Extracted Dataframe from nested JSON DataFrame

        # Look up tables loaded from motherduck as dataframes
        
        certs_df = con.sql('''
                        USE imdb_analytics;
                        USE silver;
                        
                        SELECT * FROM certificates;
                        ''').df()

        directors_df = con.sql('''
                        USE imdb_analytics;
                        USE silver;
                        
                        SELECT * FROM directors;
                        ''').df()

        # Transforms runtime column (example: '67 min' --> 67')

        new_runtime_list = []

        for item in list(media_df["Runtime"]):
            if pd.isna(item):
                new_runtime_list.append(None)
            else:
                new_runtime_list.append(int(item.split(" ")[0]))

        # Transforms Gross column by removing commas between numbers (example: '676,767,676' --> 676767676) 

        gross_list = list(media_df["Gross"])
        gross_usd_list = []

        for item in gross_list:
            
            if pd.isna(item):
                gross_usd_list.append(None)
            else:
                number_list = item.split(",")
                string_number = ""

                for number in number_list:
                    string_number += f"{number}"
                gross_usd_list.append(int(string_number))

        # Creating and Cleaning the IMDb Ranked Media DataFrame
        imdb_ranked_media_df = pd.DataFrame()
        imdb_ranked_media_df["rank"] = media_df["rank"].convert_dtypes(convert_integer=True)
        imdb_ranked_media_df["title"] = media_df["Series_Title"]
        imdb_ranked_media_df["released_year"] = pd.to_numeric(media_df["Released_Year"],errors="coerce").astype("Int64")
        imdb_ranked_media_df["poster_link"] = media_df["Poster_Link"]
        imdb_ranked_media_df["certificate_id"] = 0 # TEMP ID
        imdb_ranked_media_df["runtime_minutes"] = pd.Series(new_runtime_list)
        imdb_ranked_media_df["imdb_rating"] = pd.to_numeric(media_df["IMDB_Rating"],errors="coerce").astype("float64")
        imdb_ranked_media_df["overview"] = media_df["Overview"] 
        imdb_ranked_media_df["meta_score"] = pd.to_numeric(media_df["Meta_score"],errors="coerce").astype("Int64")
        imdb_ranked_media_df["director_id"] = 0 # TEMP ID
        imdb_ranked_media_df["no_of_votes"] = pd.to_numeric(media_df["No_of_Votes"],errors="coerce").astype("Int64")
        imdb_ranked_media_df["gross_revenue_usd"] = pd.Series(gross_usd_list)

        # Mapping certificate and director names to their database IDs
        for i in range(len(imdb_ranked_media_df)):

            # Setting certificate ids
            temp_cert_id_list = list(certs_df[media_df.iloc[i]["Certificate"] == certs_df["certificate"]]["id"])
            
            if len(temp_cert_id_list) == 1:
                cert_id = temp_cert_id_list[0]
            else:
                cert_id = None
            
            imdb_ranked_media_df.loc[i, "certificate_id"] = cert_id
            # ==================================================================

            # Setting director ids
            temp_dir_id_list = list(directors_df[media_df.iloc[i]["Director"] == directors_df["director"]]["id"])

            if len(temp_dir_id_list) == 1:
                dir_id = temp_dir_id_list[0]
            else:
                dir_id = None

            imdb_ranked_media_df.loc[i, "director_id"] = dir_id
            # ==================================================================

        # Inserting the cleaned IMDb media data into the silver database table
        con.sql("""

        USE imdb_analytics;
        USE silver;
        
        BEGIN TRANSACTION;

        """)
        
        con.register("imdb_ranked_media_data", imdb_ranked_media_df)
        
        con.sql(''' 

        INSERT INTO imdb_ranked_media (

        rank,
        title,
        released_year,
        poster_link,
        certificate_id,
        runtime_minutes,
        imdb_rating,
        overview,
        meta_score,
        director_id,
        no_of_votes,
        gross_revenue_usd
        )

        SELECT 

        rank,
        title,
        released_year,
        poster_link,
        certificate_id,
        runtime_minutes,
        imdb_rating,
        overview,
        meta_score,
        director_id,
        no_of_votes,
        gross_revenue_usd

        FROM imdb_ranked_media_data;
        
        ''')
        con.sql("COMMIT;")

        timestamp = datetime.datetime.now(datetime.timezone.utc)
        # Records the time at which the data was successfully loaded.
        # Timestamp is in UTC.

        return (f"===| IMDB RANKED MEDIA DATA LOADED INTO SILVER LAYER AT {timestamp} UTC |===\n")