# Sentiment Analysis with Twitter

**Status: First Release**

**Last Update: 28/09/2022**

## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
## General Info

The application collects tweets coming from Twitter. The relevant topic is about climate changes. The results are presented in a dashboard realized with Streamlit. 

The project is based on a big data architecture in real-time. The schema of this architecture is introduced below.

![ALT](architecture_app.png)

## Technologies

This project is created with:

- [API Twitter](!https://developer.twitter.com/en/docs/twitter-api)
- [Apache Kafka](!https://kafka.apache.org/documentation/)
- [Apache Spark](!https://spark.apache.org/)
- [Docker](!https://www.docker.com/)
- [MongoDB](!https://www.mongodb.com/)
- [vaderSentiment](!https://vadersentiment.readthedocs.io/en/latest/)
- [Streamlit](!https://streamlit.io/)

## Setup

To run this project:

```
docker compose up 
```

To run the dashboard:

```
localhost:8501
```