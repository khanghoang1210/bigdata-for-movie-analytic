from pyspark.sql import SparkSession
import logging
import logging.config
from dotenv import load_dotenv
import os
load_dotenv()



# Load the Logging Configuration File
logging.config.fileConfig(fname='./spark/utils/logging_to_file.conf')
logger = logging.getLogger(__name__)

# Declare private variables
sfURL = os.getenv("sfURL")
sfAccount = os.getenv("sfAccount")
sfUser = os.getenv("sfUser")
sfPassword = os.getenv("sfPassword")
db_user = os.getenv("db_user")
db_password = os.getenv("db_password")

SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"
def create_snowflake_table(spark, snowflake_database, snowflake_schema, df_name):
    sfOptions = {
    "sfURL": sfURL,
    "sfAccount": sfAccount,
    "sfUser": sfUser,
    "sfPassword": sfPassword,
    "sfDatabase": snowflake_database,
    "sfSchema": snowflake_schema,
    "sfWarehouse": "COMPUTE_WH",
    "sfRole": "ACCOUNTADMIN"
}
    try:
        logger.info("Creating table in snowflake!")
         # create table in snowflake
        if df_name == "movie_revenue":
            create_table = f""" CREATE TABLE IF NOT EXISTS movie_revenue (
                        id varchar,
                        rank integer,
                        revenue varchar,
                        gross_change_per_day varchar,
                        gross_change_per_week varchar,
                        crawled_date date,
                        primary key(crawled_date, id)
                    )
                    """
            
        elif df_name == "movies_detail":
                create_table = f""" CREATE TABLE IF NOT EXISTS movies_detail (
                        id varchar,
                        title varchar,
                        duration varchar,
                        rating varchar,
                        director varchar,
                        budget varchar,
                        worldwide_gross varchar,
                        genre varchar,
                        crawled_date date,
                        primary key(id)
                    )
                    """
        spark._jvm.net.snowflake.spark.snowflake.Utils.runQuery(sfOptions, create_table)
    except Exception as exp:
        logger.error("Error in the method - create_snowflake_table(). Please check the Stack Trace. " + str(exp),exc_info=True)  
    
    else:
        logger.info("Create table in snowflake - create_snowflake_table() is completed.")

def read_data_from_postgre(spark, table_name, db_user, db_password, snowflake_database,snowflake_schema):
    sfOptions = {
    "sfURL": sfURL,
    "sfAccount": sfAccount,
    "sfUser": sfUser,
    "sfPassword": sfPassword,
    "sfDatabase": snowflake_database,
    "sfSchema": snowflake_schema,
    "sfWarehouse": "COMPUTE_WH",
    "sfRole": "ACCOUNTADMIN"
    }
    try:
               
        
        logger.info("All tables is in data lake!!")
        logger.info("read_data_from_postgres() is started!")
        snowflake_df = spark.read.format(SNOWFLAKE_SOURCE_NAME) \
                .options(**sfOptions) \
                .option("dbtable",  table_name) \
                .load()

        record_count = snowflake_df.count()
        print(record_count)
        
        #handling change data capture
        if record_count == 0 or table_name == "movies_detail":
            query = f"(SELECT * FROM {table_name}) AS tmp"

        else:
               # Get latest value of crawled_date field
            last_crawled_date = snowflake_df.select("crawled_date").agg({"crawled_date": "max"}).collect()[0]["max(crawled_date)"]
            query = f"(SELECT * FROM {table_name} WHERE (crawled_date > DATE '{last_crawled_date}')) AS tmp"
    
        jdbcDF = spark.read \
                    .format("jdbc") \
                    .option("url", "jdbc:postgresql://localhost:5434/postgres") \
                    .option("dbtable", query) \
                    .option("user", db_user) \
                    .option("password", db_password) \
                    .option("driver", "org.postgresql.Driver") \
                    .load()
      
    except Exception as exp:
        logger.error("Error in the method - read_data_from_postgres(). Please check the Stack Trace. " + 
        str(exp),exc_info=True)  
    
    else:
        logger.info("Read data from postgreSQL - read_data_from_postgre() is completed.")
        return jdbcDF



def ingest_data(spark, snowflake_database, snowflake_schema, df, df_name):
    sfOptions = {
    "sfURL": sfURL,
    "sfAccount": sfAccount,
    "sfUser": sfUser,
    "sfPassword": sfPassword,
    "sfDatabase": snowflake_database,
    "sfSchema": snowflake_schema,
    "sfWarehouse": "COMPUTE_WH",
    "sfRole": "ACCOUNTADMIN"
    }
    try:
        logger.info("Ingestion - ingest_data() is started ...")
        logger.info("Writting data to Snowflake table is started...")

        save_mode = ""
        if df_name == "movies_detail":
            save_mode = 'overwrite'
        elif df_name == "movie_revenue":
            save_mode = 'append'
        # write data into data lake on snowflake
        df.write\
            .format(SNOWFLAKE_SOURCE_NAME)\
            .options(**sfOptions)\
            .option("dbtable", df_name)\
            .mode(save_mode)\
            .save()
    except Exception as exp:
        logger.error(f"Error in the method of {df_name} dataframe - ingest_data(). Please check the Stack Trace, " + str(exp), exc_info=True)
        raise
    else:
        logger.info(f"The ingest_data() function for dataframe {df_name} is completed!!")