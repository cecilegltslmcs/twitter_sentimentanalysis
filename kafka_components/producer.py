import json
from kafka import KafkaProducer
import pyfiglet
import time
import token_API
import tweepy

time.sleep(20)

###############################
#### VARIABLES DEFINITIONS ####
###############################

# API Access Token
bearer_token = token_API.bearer_token
client = tweepy.Client(bearer_token=bearer_token,
                       return_type=dict)

#Producer config
ip_server = "kafka:9092"
topic_name = 'twitter-mac'
producer = KafkaProducer(bootstrap_servers = ip_server,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

# Keywords to find in tweets
search_term = 'climate OR environment OR ClimateCrisis OR ClimateEmergency\
               OR ClimateAction OR energy OR ActOnClimate OR SaveEarth OR\
               (global AND warming) OR SaveOurOcean OR ActNow'

###############################
###########FUNCTIONS###########
###############################

def twitterAuth():
    # create the authentication object
    authenticate = tweepy.OAuth2BearerHandler(bearer_token)
    # create the API object
    api = tweepy.API(authenticate, wait_on_rate_limit=True)
    return api

class TweetListener(tweepy.StreamingClient):
    # create the streamingclient  object to collect tweets
    def on_data(self, data):
        jsonData = json.loads(data)
        dict_data= {
            'user_id' :jsonData['data']['author_id'],
            'created_at' : jsonData['data']['created_at'],
            'text': jsonData['data']['text'],
            'tweet_id': jsonData['data']['id'],
            'user_loc':  (jsonData['includes']['users'][0]['location'] if 'location' in jsonData['includes']['users'][0] else 'Null'  ) ,
            'user_name': jsonData['includes']['users'][0]['name'],
            'user_alias': jsonData['includes']['users'][0]['username'],
            'user_follower': jsonData['includes']['users'][0]['public_metrics']['followers_count'],
            'user_following': jsonData['includes']['users'][0]['public_metrics']['following_count'],
            'user_tweet_count':jsonData['includes']['users'][0]['public_metrics']['tweet_count']
        }
        print(dict_data, flush= True)
        producer.send(topic_name, value=dict_data)
        
        return True
        

    def on_error(self, status_code):
        if status_code == 420:
            return False

    def start_streaming_tweets(self, search_term):
        self.add_rules(tweepy.StreamRule(search_term))
        self.add_rules(tweepy.StreamRule("lang:en"))
        self.filter(expansions="author_id",tweet_fields=['author_id','created_at','text'],
                    user_fields = ["name", "username", "location", "public_metrics"])

if __name__ == '__main__':

    #feedback in console
    T_art = 'PRODUCER RUNNING'
    ASCII_art_1 = pyfiglet.figlet_format(T_art)
    print(ASCII_art_1, flush=True)

    #init twitter_stream class
    twitter_stream = TweetListener(bearer_token)
    twitter_stream.start_streaming_tweets(search_term)
