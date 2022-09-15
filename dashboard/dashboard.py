### create a streamlit dashboard
import pymongo
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import auth_token as auth
import time

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
@st.experimental_memo(ttl=1)
def get_data():
    db = cluster['sentiment_analysis']
    items = db['tweet_streaming'].find()
    items = list(items)  # make hashable for st.experimental_memo
    return items

st.title("Twitter sentiment analysis using the keyword 'ClimateCrisis'")
st.sidebar.title("Chart type and data")
option = st.sidebar.selectbox("Choose your analysis.", ('Home','Pie Chart', 'Distribution Chart', 'Boxplot', 'Table'))

placeholder = st.empty()

for seconds in range(2000):
    items = get_data()

    with placeholder.container():
        df = pd.DataFrame(items)
        df.drop("processed_text", axis=1, inplace=True)
        df = df.astype({'_id':str ,'text':str, 'polarity':float, 'sentiment':str})

        if option == "Home":

            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(' ')
            with col2:
                st.image("./img/Twitter-logo.png", width=150)
            with col3:
                st.write(' ')
            
            st.subheader("Welcome to the dashboard about tweets sentiments related to climate crisis. In order to choose your analysis, select an option on the sidebar.")
            st.image("./img/pxclimateaction-g25a4b047f_1920.jpg")
            st.write("Réalisé par Aurélien Blanc, Cécile Guillot & Matthieu Cavaillon")

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
                                opacity=0.7,
                                log_y=True)
            st.plotly_chart(fig2)

        if option =="Boxplot":
            y_neutral = df.loc[df["sentiment"] == "Neutral"]
            y_positive = df.loc[df["sentiment"] == "Positive"]
            y_negative = df.loc[df["sentiment"] == "Negative"]
            fig3 = go.Figure()
            fig3.add_trace(go.Box(y=y_negative.polarity, name='Negative',
                        marker_color = 'red'))
            fig3.add_trace(go.Box(y=y_neutral.polarity, name = 'Neutral',
                        marker_color = 'darkorange'))
            fig3.add_trace(go.Box(y=y_positive.polarity, name = 'Positive',
                        marker_color = 'lightgreen'))
            st.subheader("Visualisation of the statistics for each sentiment")
            st.plotly_chart(fig3)

        if option == "Table":
            st.subheader('Visualize the tweets, the polarity compound and the sentiment')
            st.dataframe(df)
            time.sleep(1)
        
        time.sleep(1)