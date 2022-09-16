import tweepy
import auth_token as auth
from kafka import KafkaProducer
import logging

"""API ACCESS KEYS"""

# consumerKey = auth.consumerKey
# consumerSecret = auth.consumerSecret
# accessToken = auth.accessToken
# accessTokenSecret = auth.accessTokenSecret
bearer_token = auth.bearerToken
ip_server = auth.bootstrap_server

producer = KafkaProducer(bootstrap_servers=ip_server)
search_term = 'Climate lang:en'
topic_name = 'twitter-mac'

client = tweepy.Client(bearer_token=bearer_token,
                       return_type=dict)

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
