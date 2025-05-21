import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import base64

st.title ("Movies Analysis")

# Load datasets


encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']

for encoding in encodings_to_try:
    try:
        movies = pd.read_csv("movies.csv", encoding=encoding)
        ratings = pd.read_csv('rating.csv', encoding=encoding)
        tags = pd.read_csv('tags.csv', encoding=encoding)
        print(f"Successfully loaded with {encoding} encoding")
        break
    except UnicodeDecodeError:
        continue
else:
    raise ValueError("None of the encodings worked for your files") 

