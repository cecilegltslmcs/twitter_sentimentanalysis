from kafka import KafkaConsumer
from pymongo import MongoClient
import json
import auth_token as auth

# Connect to MongoDB and database
try:
<<<<<<< HEAD
   cluster = pymongo.MongoClient("mongodb+srv://auth.mongo_user:auth.mongo_password@cluster0.g0zvq8k.mongodb.net/?retryWrites=true&w=majority")
=======
   cluster = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.g0zvq8k.mongodb.net/?retryWrites=true&w=majority")
>>>>>>> f68b96b7ef0f2a431cf35c54ce3d4b09693056c4
   db = cluster['sentiment_analysis']
   collection = db["raw_tweet"]
   print("Connected successfully!")
except:  
   print("Could not connect to MongoDB")
    

topic_name = 'twitter-mac'
ip_server = auth.bootstrap_server

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
data_sender = []
#Wait to have nb_upload tweets before updating the DB to limit the nb of connections
nb_upload = 10
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
<<<<<<< HEAD
      data_sender = []
=======
      data_sender = []

>>>>>>> f68b96b7ef0f2a431cf35c54ce3d4b09693056c4