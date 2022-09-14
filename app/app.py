from pyspark.sql import functions as F
from pyspark.sql.functions import explode
from pyspark.sql.functions import split
from pyspark.sql.types import StringType, StructType, StructField, FloatType
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.ml.feature import RegexTokenizer
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

ip_server="51.38.185.58:9092"

def cleanTweet(tweet: str) -> str:
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
    my_punctuation = '!"$%&\'()*+,-./:;<=>?[\\]^_`{|}~•@â'
    tweet = re.sub('[' + my_punctuation + ']+', ' ', str(tweet))

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
    elif polarityValue > -0.05 & polarityValue < 0.05:
        return 'Neutral'
    else:
        return 'Positive'

if __name__ == "__main__":
    spark = SparkSession \
        .builder \
        .appName("TwitterSentimentAnalysis") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2") \
        .getOrCreate()

    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", ip_server) \
        .option("subscribe", "twitter") \
        .load()

    mySchema = StructType([StructField("text", StringType(), True)])
    # Get only the "text" from the information we receive from Kafka. The text is the tweet produce by a user
    values = df.select(from_json(df.value.cast("string"), mySchema).alias("tweet"))

    df1 = values.select("tweet.*")
    clean_tweets = F.udf(cleanTweet, StringType())
    raw_tweets = df1.withColumn('processed_text', clean_tweets(col("text")))
    # udf_stripDQ = udf(stripDQ, StringType())

    polarity = F.udf(getPolarity, FloatType())
    sentiment = F.udf(getSentiment, StringType())

    polarity_tweets = raw_tweets.withColumn("polarity", polarity(col("processed_text")))
    sentiment_tweets = polarity_tweets.withColumn("sentiment", sentiment(col("polarity")))

    '''
    all about tokenization
    '''
    # Create a tokenizer that Filter away tokens with length < 3, and get rid of symbols like $,#,...
    tokenizer = RegexTokenizer()\
                .setPattern("[\\W_]+")\
                .setMinTokenLength(3)\
                .setInputCol("processed_text")\
                .setOutputCol("tokens")

    # Tokenize tweets
    tokenized_tweets = tokenizer\
                       .transform(raw_tweets)

    tweets_df = df1\
                .withColumn('word', explode(split(col("text"), ' ')))\
                .groupby('word')\
                .count()\
                .sort('count', ascending=False)\
                .filter(col('word')\
                .contains('#'))

    query = sentiment_tweets\
            .writeStream\
            .queryName("test_tweets") \
            .output("append")\
            .format("console")\
            .option("truncate", False)\
            .start()\
            .awaitTermination(60)