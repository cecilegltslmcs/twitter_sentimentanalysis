"""Spark job which collect, clean & analyze contains of tweets"""

import database_auth as auth
import findspark
import pyfiglet
import pymongo
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, FloatType
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StringType, StructType, StructField, FloatType
import re
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

time.sleep(10)
findspark.init()

# variables settings for kafka and mongodb
ip_server = "kafka:9092"
topic_name = "twitter-mac"
user = auth.user
password = auth.password
uri = "mongodb://{}:{}@mongodb:27017".format(user, password)

# initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

###############################
###########FUNCTIONS###########
###############################

 ##### Processing tweets ######

def cleanTweet(tweet: str):
    """This function cleans the tweets before
    performing sentiment analysis of the tweet.

    Input: tweets coming from Kafka.

    Output: tweets cleaning ready for the sentiment analysis."""

    # remove links
    tweet = re.sub(r'http\S+', '', str(tweet))
    tweet = re.sub(r'bit.ly/\S+', '', str(tweet))
    tweet = tweet.strip('[link]')

    # remove users
    tweet = re.sub('(RT\s@[A-Za-z]+[A-Za-z0-9-_]+)', '', str(tweet))
    tweet = re.sub('(@[A-Za-z]+[A-Za-z0-9-_]+)', '', str(tweet))

    # remove punctuation
    my_punctuation = '"$%&\'()*+,-./:;<=>?[\\]^_`{|}~•@â'
    tweet = re.sub('[' + my_punctuation + ']+', '', str(tweet))

    # remove number
    tweet = re.sub('([0-9]+)', '', str(tweet))

    # remove hashtag
    tweet = re.sub('(#[A-Za-z]+[A-Za-z0-9-_]+)', '', str(tweet))

    return tweet

def getPolarity(tweet):
    score = analyzer.polarity_scores(tweet)["compound"]
    return score

def getSentiment(polarityValue):
    if polarityValue <= -0.05:
        return 'Negative'
    elif (polarityValue > -0.05) & (polarityValue < 0.05):
        return 'Neutral'
    else:
        return 'Positive'

###### MongoDB Settings ######       
class WriteRowMongo:
    def open(self, partition_id, epoch_id):
        self.myclient = pymongo.MongoClient(uri)
        self.mydb = self.myclient["sentiment_analysis"]
        self.mycol = self.mydb["tweet_streaming"]
        return True

    def process(self, row):
        self.mycol.insert_one(row.asDict())

    def close(self, error):
        self.myclient.close()
        return True

if __name__ == "__main__":

    # initialize sparkSession & sparkContext
    spark = (SparkSession
        .builder
        .master('spark://spark:7077')
        .config("spark.mongodb.input.uri", uri)
        .config("spark.mongodb.output.uri", uri)
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2")
        .appName("TwitterSentimentAnalysis")
        .getOrCreate())
    sc = spark.sparkContext.setLogLevel("ERROR")

    # read Kafka stream
    df = (spark
        .readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", ip_server)
        .option("subscribe", topic_name)
        .load()
        )

    # Schema definition & data selection
    mySchema = StructType([StructField("text", StringType(), True)])
    mySchema2 = StructType([StructField("created_at", StringType(), True)])
    values = df.select(
    from_json(df.value.cast("string"), mySchema).alias("tweet"),
    from_json(df.value.cast("string"), mySchema2).alias("date"),
        )
    df1 = values.select("tweet.*", "date.*")

    # Cleaning tweets & sentiment analysis
    clean_tweets = F.udf(cleanTweet, StringType())
    raw_tweets = df1.withColumn('processed_text', clean_tweets(col("text")))
    polarity = F.udf(getPolarity, FloatType())
    sentiment = F.udf(getSentiment, StringType())
    polarity_tweets = raw_tweets.withColumn("polarity", polarity(col("processed_text")))
    sentiment_tweets = polarity_tweets.withColumn("sentiment", sentiment(col("polarity")))

    # console display (debug mode)
    # query = (sentiment_tweets
    #         .writeStream
    #         .queryName("test_tweets")
    #         .outputMode("append")
    #         .format("console")
    #         .start()
    #         .awaitTermination())

    # parquet file dumping
    # parquet = sentiment_tweets.repartition(1)
    # query = (parquet
    #     .writeStream
    #     .queryName("final_tweets_parquet")
    #     .outputMode("append").format("parquet")
    #     .option("path", "./parquet_save")
    #     .option("checkpointLocation", "./check")
    #     .trigger(processingTime='60 seconds')
    #     .start()
    #     .awaitTermination())

    # mongodb dumping
    T_art = 'COLLECT TWEETS IN PROGRESS...'
    ASCII_art_1 = pyfiglet.figlet_format(T_art)
    print(ASCII_art_1, flush=True)
    query = (sentiment_tweets
                .writeStream
                .foreach(WriteRowMongo())
                .start()
                .awaitTermination())
