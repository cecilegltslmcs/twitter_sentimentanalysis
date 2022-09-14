import tweepy
from kafka import KafkaProducer
import logging

"""API ACCESS KEYS"""

# consumerKey = "consumerKey"
# consumerSecret = "consumerSecret"
# accessToken = "accessToken"
# accessTokenSecret = "accessTokenSecret"
bearer_token = "AAAAAAAAAAAAAAAAAAAAAOOcgwEAAAAA1hJMtyYRRJ4YChdYhyXTkL0uldE%3DNVax1u4M5cROmdTKLpi32uHR9pUGB28QQz2FhcIXAqQSkNxHF1"
ip_server = "51.38.185.58:9092" 

producer = KafkaProducer(bootstrap_servers=ip_server)
search_term = 'ClimateCrisis'
topic_name = 'twitter'

client = tweepy.Client(bearer_token=bearer_token)

def twitterAuth():
    # create the authentication object
    authenticate = tweepy.OAuth2BearerHandler(bearer_token)
    ## set the access token and the access token secret
    #authenticate.set_access_token(accessToken, accessTokenSecret)
    # create the API object
    api = tweepy.API(authenticate, wait_on_rate_limit=True)
    return api


class TweetListener(tweepy.StreamingClient):

    def on_data(self, raw_data):
        logging.info(raw_data)
        producer.send(topic_name, value=raw_data)
        return True

    def on_error(self, status_code):
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False

    def start_streaming_tweets(self, search_term):
        self.add_rules(tweepy.StreamRule(search_term))
        self.filter()
        #self.filter(track=search_term, stall_warnings=True, languages=["en"])


if __name__ == '__main__':
    #init twitter_stream class
    twitter_stream = TweetListener(bearer_token)
        
    twitter_stream.start_streaming_tweets(search_term)
