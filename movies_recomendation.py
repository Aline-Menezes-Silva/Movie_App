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
