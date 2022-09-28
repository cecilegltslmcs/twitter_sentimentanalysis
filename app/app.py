from pyspark.sql import functions as F
from pyspark.sql.types import StringType, FloatType
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StringType, StructType, StructField, FloatType
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import findspark
import time
import pymongo

time.sleep(10)

findspark.init()

ip_server = "kafka:9092"
topic_name = "twitter-mac"
uri = "mongodb://root:example@mongodb:27017"

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
    spark = (SparkSession
        .builder
        .master('spark://spark:7077')
        .config("spark.mongodb.input.uri", uri)
        .config("spark.mongodb.output.uri", uri)
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2")
        .appName("TwitterSentimentAnalysis")
        .getOrCreate())
    sc = spark.sparkContext.setLogLevel("ERROR")

    df = (spark
        .readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", ip_server)
        .option("subscribe", topic_name)
        .load()
        )

    mySchema = StructType([StructField("text", StringType(), True)])
    mySchema2 = StructType([StructField("created_at", StringType(), True)])

    values = df.select(
    from_json(df.value.cast("string"), mySchema).alias("tweet"),
    from_json(df.value.cast("string"), mySchema2).alias("date"),
        )

    df1 = values.select("tweet.*", "date.*")

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
    query= (sentiment_tweets
                .writeStream
                .foreach(WriteRowMongo())
                .start()
                .awaitTermination())
