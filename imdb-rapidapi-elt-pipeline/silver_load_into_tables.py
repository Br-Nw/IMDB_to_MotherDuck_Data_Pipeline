import duckdb
import pandas as pd
import datetime


def load_silver_lookup_tables(motherduck_token):

    with duckdb.connect(f'md:?motherduck_token={motherduck_token}') as con:
        raw_movie_df = con.sql("SELECT * FROM imdb_analytics.bronze.raw_movie_data;").df() # Nested bronze data loaded as a DataFrame

    df = pd.DataFrame.from_dict(list(raw_movie_df["result"])) # Extracted Dataframe from nested JSON DataFrame

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

    # DataFrames containing unique values for movie lookup tables.
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

    return (f"===| DIRECTORS, STARS, CERTIFICATES, AND GENRES LOADED INTO SILVER LAYER AT {timestamp} UTC |===\n")