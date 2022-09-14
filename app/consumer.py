from kafka import KafkaConsumer
import json

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

for message in consumer:
    tweets = json.loads(json.dumps(message.value))
    print(tweets)