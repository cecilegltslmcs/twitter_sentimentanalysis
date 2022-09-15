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

st.title('Twitter sentiment analysis')

st.markdown('''Twitter sentiment analysis using the keyword ClimateCrisis''')


st.sidebar.title("Chart type and data")
option = st.sidebar.selectbox("which Dashboard?", ('Pie Chart', 'Distribution Chart', 'Table'))


df = pd.DataFrame(items)
df = df.astype({'_id':str,'text':str, 'processed_text':str,'polarity':float, 'sentiment':str })
#display data

if option == "Table":
    st.write(df.head())

if option == 'Pie Chart':
    sentiment_count = df.groupby(['sentiment']).agg(nb_sentiment=pd.NamedAgg(column="sentiment", aggfunc="count")).reset_index()

    #plotly
    #Pie chart of the sentiment count
    colors = ['red', 'darkorange', 'lightgreen']
    fig = go.Figure(data=[go.Pie(
                             labels=sentiment_count.sentiment,
                             values=sentiment_count.nb_sentiment)])
    fig.update_traces(hoverinfo='value', textinfo='label+percent', textfont_size=20,
                  marker=dict(colors=colors))
    st.plotly_chart(fig)

if option =='Distribution Chart':
    #distribution chart
    distribution_df = df[['polarity']].sort_values(by='polarity')
    #st.write(distribution_df)
    fig2 = px.scatter(distribution_df,x=df.index, y='polarity')
    st.plotly_chart(fig2)
