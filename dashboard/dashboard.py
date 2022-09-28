import database_auth as auth
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import streamlit as st
import time
from wordcloud import WordCloud, STOPWORDS

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
option = st.sidebar.selectbox("Choose your analysis.", ('Home', 'Data', 'Pie Chart', 'Distribution Chart', 'Boxplot', 'Wordcloud'))

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

        if option == "Data":
            counts = len(df.index)
            st.subheader('Visualisation of the data coming from the database and the number of tweets')
            st.write("Number of tweets:", counts)
            st.dataframe(df)

        if option == 'Pie Chart':
            col1,col2 = st.columns(2)
            with col1:
                st.subheader("Distribution of the different sentiment in the tweets")
                sentiment_count = df.groupby(['sentiment']).agg(nb_sentiment=pd.NamedAgg(column="sentiment", aggfunc="count")).reset_index()
                colors = ['indianred', 'lightgray', 'lightgreen']
                fig11 = go.Figure(data=[go.Pie(labels=sentiment_count.sentiment,values=sentiment_count.nb_sentiment)])
                fig11.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                fig11.update_traces(hoverinfo='percent', textinfo='label+value', textfont_size=15, marker=dict(colors=colors))
                st.plotly_chart(fig11)
            
            with col2 :
                st.subheader("Tweet by sentiment and by account size")
                
                def small_medium_big(x):
                    res = "big"
                    if x < 100 :
                        res = "small"
                    elif x < 1000 :
                        res = "medium"
                    return res
                
                df['account_size'] = df['user_follower'].apply(small_medium_big)
                sentiment_size = df.groupby(['sentiment','account_size']).size().reset_index(name='nb_tweet')
            fig12 = px.histogram(sentiment_size, x='account_size', y='nb_tweet',
                                    color='sentiment', barmode='group')
            st.plotly_chart(fig12)

        if option =="Distribution Chart":
            col1, col2 = st.columns(2)
            with col1 :
                st.subheader("Number of tweets by polarity")
                fig21 = px.histogram(df, x="polarity", opacity=0.7, log_y=True)
                st.plotly_chart(fig21)
            with col2:
                st.subheader('Tweet polarity by datetime')
                fig22 = px.line(df.sort_values(by='created_at'), x='created_at', y='polarity')
                st.plotly_chart(fig22)

        if option =="Boxplot":
            y_neutral = df.loc[df["sentiment"] == "Neutral"]
            y_positive = df.loc[df["sentiment"] == "Positive"]
            y_negative = df.loc[df["sentiment"] == "Negative"]
            fig3 = go.Figure()
            fig3.add_trace(go.Box(y=y_negative.polarity, name='Negative', marker_color = 'indianred'))
            fig3.add_trace(go.Box(y=y_neutral.polarity, name = 'Neutral', marker_color = 'lightgray'))
            fig3.add_trace(go.Box(y=y_positive.polarity, name = 'Positive', marker_color = 'lightgreen'))
            fig3.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.subheader("Visualisation of the statistics for each sentiment")
            st.plotly_chart(fig3)

        if option == "Wordcloud":
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
