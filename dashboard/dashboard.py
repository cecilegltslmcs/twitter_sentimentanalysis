### create a streamlit dashboard
import pymongo
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import auth_token as auth

#connection to the cluster
# Connect to MongoDB and database

@st.experimental_singleton
def init_connection():
    return pymongo.MongoClient(auth.uri_mongo_2)

try:
    cluster = init_connection()
    print('Connection OK')
except:
    print('Connection error')
    
# Pull data from the collection.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def get_data():
    db = cluster['sentiment_analysis']
    items = db['tweet_streaming'].find()
    items = list(items)  # make hashable for st.experimental_memo
    return items

items = get_data()

st.title("Twitter sentiment analysis using the keyword 'ClimateCrisis'")

st.sidebar.title("Chart type and data")
option = st.sidebar.selectbox("Choose your analysis.", ('Pie Chart', 'Distribution Chart', 'Boxplot', 'Table'))


df = pd.DataFrame(items)
df.drop("processed_text", axis=1, inplace=True)
df = df.astype({'_id':str ,'text':str, 'polarity':float, 'sentiment':str})

if option == 'Pie Chart':
    st.subheader("Distribution of the different sentiment in the tweets")
    sentiment_count = df.groupby(['sentiment']).agg(nb_sentiment=pd.NamedAgg(column="sentiment", aggfunc="count")).reset_index()

    colors = ['red', 'darkorange', 'lightgreen']
    fig = go.Figure(data=[go.Pie(
                             labels=sentiment_count.sentiment,
                             values=sentiment_count.nb_sentiment)])
    fig.update_traces(hoverinfo='value', textinfo='label+percent', textfont_size=15,
                      marker=dict(colors=colors))
    st.plotly_chart(fig)

if option =="Distribution Chart":
    st.subheader("Number of tweets by polarity")
    fig2 = px.histogram(df,
                        x="polarity",
                        log_y=True)
    st.plotly_chart(fig2)

if option =="Boxplot":
    st.subheader("Visualisation of the statistics for each sentiment")
    fig3 = px.box(df, x="sentiment",
                      y="polarity")
    st.plotly_chart(fig3)

if option == "Table":
    st.subheader('Visualize the tweets, the polarity compound and the sentiment')
    st.dataframe(df)