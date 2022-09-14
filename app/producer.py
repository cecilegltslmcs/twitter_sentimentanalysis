import tweepy
from kafka import KafkaProducer
import logging

"""API ACCESS KEYS"""

consumerKey = "consumerKey"
consumerSecret = "consumerSecret"
accessToken = "accessToken"
accessTokenSecret = "accessTokenSecret"

ip_server = "51.38.185.58:9092" 

producer = KafkaProducer(bootstrap_servers=ip_server)
search_term = 'ClimateCrisis'
topic_name = 'twitter'

client = tweepy.Client(
    consumer_key = consumerKey,
    consumer_secret = consumerSecret,
    access_token = accessToken,
    access_token_secret = accessTokenSecret
)

def twitterAuth():
    # create the authentication object
    authenticate = tweepy.OAuthHandler(consumerKey, consumerSecret)
    # set the access token and the access token secret
    authenticate.set_access_token(accessToken, accessTokenSecret)
    # create the API object
    api = tweepy.API(authenticate, wait_on_rate_limit=True)
    return api


class TweetListener(tweepy.Stream):

    def on_data(self, raw_data):
        logging.info(raw_data)
        producer.send(topic_name, value=raw_data)
        return True

    def on_error(self, status_code):
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False

    def start_streaming_tweets(self, search_term):
        self.filter(track=search_term, stall_warnings=True, languages=["en"])


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    twitter_stream = TweetListener(consumerKey, consumerSecret, accessToken, accessTokenSecret)
    twitter_stream.start_streaming_tweets(search_term)