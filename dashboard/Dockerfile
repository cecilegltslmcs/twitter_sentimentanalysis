FROM ubuntu:latest

RUN apt-get update &&\
    apt-get install -y python3 &&\
    python3-pip -y &&\
    pip install -r requirements.txt

WORKDIR /home/user

COPY dashboard.py dashboard.py

CMD streamlit run dashboard.py