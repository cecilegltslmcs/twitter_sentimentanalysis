import database_auth as auth
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import streamlit as st
import time
from wordcloud import WordCloud, STOPWORDS

def small_medium_big(x):
    res = "big"
    if x < 100 :
        res = "small"
    elif x < 1000 :
        res = "medium"
    return res

#connect to MongoDB and database
@st.experimental_singleton
def init_connection():
    return MongoClient(auth.uri_mongo)

try:
    client = init_connection()
    print('Connection OK')
except:
    print('Connection error')

# Pull data from the collection
@st.experimental_memo(ttl=1)
def get_data():
    db = client['sentiment_analysis']
    items = db['tweet_streaming'].find()
    items = list(items)
    return items

st.title("Twitter sentiment analysis using different keywords related to the Climate and the Environment")
st.sidebar.title("Chart type and data")
option = st.sidebar.selectbox("Choose your analysis.", ('Home', 'Tweets', 'Sentiment Analysis Repartition', 'Polarity Score Repartition', 'Statistics Description', 'Content Illustration'))

if option == "Home":
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(' ')
    with col2:
        st.image("img/Twitter-logo.png", width=150)
    with col3:
        st.write(' ')
    st.header("Welcome to the dashboard about tweets sentiments related to climate crisis.\
               In order to choose your analysis, select an option on the sidebar.")
    st.image("img/pxclimateaction-g25a4b047f_1920.jpg")
    st.write("Réalisé par Aurélien Blanc, Cécile Guillot & Matthieu Cavaillon")

placeholder = st.empty()
    
while True:
    items = get_data()
    
    with placeholder.container():
    
        df = pd.DataFrame(items)
        df = df.astype({'_id':str ,'text':str, "processed_text": str, 'polarity':float, 'sentiment':str})

        if option == "Tweets":
            counts = len(df.index)
            st.subheader('Number of tweets and general information')
            st.write("Number of tweets:", counts)
            st.dataframe(df)

        if option == 'Sentiment Analysis Repartition':
            st.subheader("Tweets by sentiment")
            sentiment_count = df.groupby(['sentiment']).agg(nb_sentiment=pd.NamedAgg(column="sentiment", aggfunc="count")).reset_index()
            fig11 = go.Figure(data=[go.Pie(labels=sentiment_count.sentiment,values=sentiment_count.nb_sentiment)])
            fig11.update_traces(hoverinfo='percent', textinfo='label+value', textfont_size=15)
            st.plotly_chart(fig11)
            
            st.subheader("Tweets by sentiment and by account size")
            df['account_size'] = df['user_follower'].apply(small_medium_big)
            sentiment_size = df.groupby(['sentiment','account_size']).size().reset_index(name='nb_tweet')
            fig12 = px.histogram(sentiment_size, x='account_size', y='nb_tweet',
                                 color='sentiment', barmode='group')
            st.plotly_chart(fig12)

        if option =="Polarity Score Repartition":
            st.subheader("Number of tweets by polarity")
            fig21 = px.histogram(df, x="polarity", opacity=0.7, log_y=True)
            st.plotly_chart(fig21)

            st.subheader('Tweet polarity by datetime')
            fig22 = px.line(df.sort_values(by='created_at'), x='created_at', y='polarity')
            st.plotly_chart(fig22)

        if option =="Statistics Description":
            y_neutral = df.loc[df["sentiment"] == "Neutral"]
            y_positive = df.loc[df["sentiment"] == "Positive"]
            y_negative = df.loc[df["sentiment"] == "Negative"]
            fig3 = go.Figure()
            fig3.add_trace(go.Box(y=y_negative.polarity, name='Negative'))
            fig3.add_trace(go.Box(y=y_neutral.polarity, name = 'Neutral'))
            fig3.add_trace(go.Box(y=y_positive.polarity, name = 'Positive'))
            fig3.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.subheader("Visualisation of the statistics for each sentiment")
            st.plotly_chart(fig3)
            st.dataframe(df.groupby("sentiment").describe())

        if option == "Content Illustration":
            fig4, ax = plt.subplots()     
            words = ' '.join(df['processed_text'])
            wordcloud = WordCloud(stopwords=STOPWORDS,\
                                  background_color='white',\
                                  width=800, height=640).generate(words)
            ax.imshow(wordcloud, interpolation = 'bilinear')
            ax.axis("off")
            st.subheader("Visualisation of the wordCloud")
            st.write(fig4)
        
        time.sleep(1)
