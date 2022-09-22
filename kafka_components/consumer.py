from kafka import KafkaConsumer
from pymongo import MongoClient
import json
import auth_token as auth

# Connect to MongoDB and database
try:
   cluster = MongoClient(auth.uri_mongo_2)
   db = cluster['sentiment_analysis']
   collection = db["raw_tweet"]
   print("Connected successfully!")
except:
   print("Could not connect to MongoDB")
    
topic_name = 'twitter-mac'
ip_server = auth.bootstrap_server
# ip_server = "51.38.185.58:9092" 


consumer = KafkaConsumer(
     topic_name,
     bootstrap_servers=[ip_server],
     value_deserializer=lambda x: json.loads(x.decode('utf-8')))


# Parse received data from Kafka
data_sender = []
#Wait to have nb_upload tweets before updating the DB to limit the nb of connections
nb_upload = 3
k=0
for msg in consumer:
   record = json.loads(json.dumps(msg.value))
   print(record)
   data = record['data']

   data_sender.append(record['data'])
   k += 1
   if k >= nb_upload:
   # Ingest data into MongoDB
      try:
         collection.insert_many(data_sender)
         print("Data inserted into MongoDB")
      except:
         print("Could not insert into MongoDB") 
   k=0
   data_sender = []