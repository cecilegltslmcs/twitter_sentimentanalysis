from kafka import KafkaConsumer
from pymongo import MongoClient
import json

# Connect to MongoDB and database
try:
   client = MongoClient('localhost', 27017)
   db = client.raw_tweet
   print("Connected successfully!")
except:  
   print("Could not connect to MongoDB")
    

topic_name = 'twitter-mac'
ip_server = "51.38.185.58:9092"

consumer = KafkaConsumer(
    topic_name,
     bootstrap_servers=[ip_server],
     auto_offset_reset='latest',
     enable_auto_commit=True,
     auto_commit_interval_ms=5000,
     fetch_max_bytes=128,
     max_poll_records=100,
     value_deserializer=lambda x: json.loads(x.decode('utf-8')))


# Parse received data from Kafka
for msg in consumer:
    record = json.loads(json.dumps(msg.value))
    print(record)
    data = record['data']
    
    # Create dictionary and ingest data into MongoDB
    try:
       tweet_rec = {'data':data}
       rec_id1 = db.coba_info.insert_one(tweet_rec)
       print("Data inserted with record ids", rec_id1)
    except:
       print("Could not insert into MongoDB")