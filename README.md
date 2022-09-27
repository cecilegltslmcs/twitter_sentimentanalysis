# Sentiment Analysis with Twitter

**Status: In Progress**

**Last Update: 15/09/2022**

*French Version below*

## Objectives

The aim of this project is to realize a sentiment analysis related to a specific topic. This sentiment analysis will be performed on tweets collected by the Twitter API v2. In order to realize this project, different steps are necessary : collecting data in streaming coming from Twitter, performing a real-time processing to annotate the tweets and storage the results in a database. Different tools will be used: 
- [API Twitter](!https://developer.twitter.com/en/docs/twitter-api)
- [Apache Kafka](!https://kafka.apache.org/documentation/)
- [Apache Spark](!https://spark.apache.org/)
- [MongoDB](!https://www.mongodb.com/)
- [vaderSentiment](!https://vadersentiment.readthedocs.io/en/latest/)
- [Streamlit](!https://streamlit.io/)

## Architecture

A kappa/lambda architecture will be build.

![ALT](architecture_app.png)

***
## Objectif du projet

Le but de ce projet est de réaliser une analyse de sentiments à partir d'une thématique définie au préalable. Cette analyse de sentiments sera réalisée sur des tweets récupérées via l'API v2 Twitter. Pour cela, il va falloir collecter les données en temps réel à partir de Twitter, effectuer un traitement en direct des messages pour leur attribuer un sentiment et enfin stocker les résultats dans une base de données. Les outils utilisés sont les suivants :
- [API Twitter](!https://developer.twitter.com/en/docs/twitter-api)
- [Apache Kafka](!https://kafka.apache.org/documentation/)
- [Apache Spark](!https://spark.apache.org/)
- [MongoDB](!https://www.mongodb.com/)
- [vaderSentiment](!https://vadersentiment.readthedocs.io/en/latest/)
- [Streamlit](!https://streamlit.io/)

## Choix de l'architecture

Pour ce projet nous avons choisi d'utiliser une architecture kappa. Ce choix permet de traiter les tweets en temps réel tout en gardant une trace des tweets originaux dans une autre collection de notre base de donnée.

Les tweets sont tout d'abord récupérés via l'API puis distribués à la base de donnée et à l'algorithme de machine learning via un consumer Kafka.
On obtient ainsi une seule application Spark qui s'occupe de la partie machine learning. On évite ainsi la présence d'une deuxième application spark chargée uniquement de diriger les tweets vers notre base de donnée. Ainsi notre application gagne en rapidité.

Une fois les tweets nettoyés et analysés par notre algorithme, les informations sont stockées à leur tour dans une base de donnée NoSQL (ici, MongoDB) et peuvent être analysées en temps réelle vià un dashboard Streamlit.

## Schéma de l'architecture

![ALT](architecture_app.png)