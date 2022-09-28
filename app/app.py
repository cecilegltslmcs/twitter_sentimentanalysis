from pyspark.sql import functions as F
from pyspark.sql.types import StringType, FloatType
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StringType, FloatType
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import findspark
import time

time.sleep(30)

findspark.init()

ip_server = "kafka:9092"
topic_name = "twitter-mac"

analyzer = SentimentIntensityAnalyzer()

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

def write_row(batch_df , batch_id):
    (batch_df
        .write
        .format("mongo")
        .mode("update")
        .save())
    pass

if __name__ == "__main__":
    spark = (SparkSession
        .builder
        .master("spark://spark:7077")
        .config("spark.mongodb.input.uri", "mongodb://mongo:27017/sentiment_analysis.tweet_streaming?readPreference=primaryPreferred")
        .config("spark.mongodb.output.uri", "mongodb://mongo:27017/sentiment_analysis.tweet_streaming")
        .config("spark.jars.packages","org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0")
        .config("spark.jars.packages","org.mongodb.spark:mongo-spark-connector_2.12:3.0.1")
        .appName("TwitterSentimentAnalysis")
        .getOrCreate())
    sc = spark.sparkContext.setLogLevel("ERROR")
    
    raw_json = spark.read.json("tweet.json",\
                                multiLine=True)
    df = (spark
        .readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", ip_server)
        .option("subscribe", topic_name)
        .load()
        .withColumn("value", from_json(col("value").cast("string"), raw_json.schema))
        .select(col('value.data.text')))

    clean_tweets = F.udf(cleanTweet, StringType())
    raw_tweets = df.withColumn('processed_text', clean_tweets(col("text")))

    polarity = F.udf(getPolarity, FloatType())
    sentiment = F.udf(getSentiment, StringType())

    polarity_tweets = raw_tweets.withColumn("polarity", polarity(col("processed_text")))
    sentiment_tweets = polarity_tweets.withColumn("sentiment", sentiment(col("polarity")))

    # console display (debug mode)
    """query = (sentiment_tweets
            .writeStream
            .queryName("test_tweets")
            .outputMode("append")
            .format("console")
            .start()
            .awaitTermination())"""
              
    """# parquet file dumping
    parquet = sentiment_tweets.repartition(1)
    query2 = (parquet
        .writeStream
        .queryName("final_tweets_parquet")
        .outputMode("append").format("parquet")
        .option("path", "./parquet_save")
        .option("checkpointLocation", "./check")
        .trigger(processingTime='60 seconds')
        .start()
        .awaitTermination())"""

    # mongodb dumping
    query = (sentiment_tweets
            .writeStream
            .foreachBatch(write_row)
            .start()
            .awaitTermination())
