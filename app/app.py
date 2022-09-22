from pyspark.sql import functions as F
import auth_token as auth
from pyspark.sql.types import StringType, FloatType
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import findspark

findspark.init()

ip_server = "localhost:9092"
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
    batch_df\
        .write\
        .format("mongo")\
        .mode("append")\
        .save()
    pass

if __name__ == "__main__":
    spark = SparkSession \
        .builder \
        .config("spark.mongodb.input.uri", auth.uri_mongo)\
        .config("spark.mongodb.output.uri", auth.uri_mongo)\
        .appName("TwitterSentimentAnalysis") \
        .getOrCreate()
    
    sc = spark.sparkContext.setLogLevel("ERROR")

    raw_json = spark.read.json("tweet.json",\
                                multiLine=True)

    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", ip_server)\
        .option("subscribe", topic_name) \
        .load()\
        .withColumn("value", from_json(col("value").cast("string"), raw_json.schema))\
        .select(col('value.data.text'))

    clean_tweets = F.udf(cleanTweet, StringType())
    raw_tweets = df.withColumn('processed_text', clean_tweets(col("text")))

    polarity = F.udf(getPolarity, FloatType())
    sentiment = F.udf(getSentiment, StringType())

    polarity_tweets = raw_tweets.withColumn("polarity", polarity(col("processed_text")))
    sentiment_tweets = polarity_tweets.withColumn("sentiment", sentiment(col("polarity")))

    """ # console display (debug mode)
    query = sentiment_tweets\
            .writeStream\
            .queryName("test_tweets") \
            .outputMode("append")\
            .format("console")\
            .start()\
            .awaitTermination()"""
    
    """# parquet file dumping
    parquet = sentiment_tweets.repartition(1)
    query2 = parquet \
        .writeStream \
        .queryName("final_tweets_parquet") \
        .outputMode("append").format("parquet") \
        .option("path", "./parquet_save") \
        .option("checkpointLocation", "./check") \
        .trigger(processingTime='60 seconds')\
        .start()\
        .awaitTermination()"""

    # mongodb dumping
    query = sentiment_tweets\
            .writeStream\
            .foreachBatch(write_row)\
            .start()\
            .awaitTermination()