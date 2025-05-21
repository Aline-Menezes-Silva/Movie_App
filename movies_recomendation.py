import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Load datasets with multiple encoding support
encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']

for encoding in encodings_to_try:
    try:
        movies = pd.read_csv("movies.csv", encoding=encoding)
        ratings = pd.read_csv('rating.csv', encoding=encoding)
        tags = pd.read_csv('tags.csv', encoding=encoding)
        break
    except UnicodeDecodeError:
        continue
else:
    st.error("None of the encodings worked for your files.")
    st.stop()

# Preprocessing
movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')
movies['year'] = pd.to_numeric(movies['year'], errors='coerce')
movies['genres_list'] = movies['genres'].str.split('|')

genre_popularity = movies.explode('genres_list').groupby('genres_list').size().reset_index(name='count')
genre_popularity = genre_popularity.sort_values('count', ascending=False)

movie_stats = ratings.groupby('movieId').agg(
    avg_rating=('rating', 'mean'),
    rating_count=('rating', 'count'),
    rating_std=('rating', 'std')
).fillna(0)

tag_stats = tags.groupby('movieId').agg(
    tag_count=('tag', 'count'),
    unique_taggers=('userId', 'nunique')
).fillna(0)

movie_stats = movies.merge(movie_stats, on='movieId', how='left')\
                    .merge(tag_stats, on='movieId', how='left')\
                    .fillna(0)

# UI Configuration
st.set_page_config(page_title="FilmFilter Dashboard", layout="wide")

# Color Scheme
colors = {
    'background': '#1E3A5F',
    'text': '#f8f9fa',
    'green': '#00AA55',
    'orange': '#FF6B00',
    'gold': '#FFC233',
    'blue': '#3A7BFF',
    'yellow': '#FFD700',
    'blue1': '#5A7BDE'
}

# Header
st.markdown(f"<h1 style='text-align:center; color:{colors['text']};'>FilmFilter Dashboard</h1>", unsafe_allow_html=True)
st.markdown("## Explore movie trends and patterns", unsafe_allow_html=True)

# Sidebar - Filters
st.sidebar.header("Filter Options")

genre_options = genre_popularity['genres_list'].head(15).tolist()
selected_genres = st.sidebar.multiselect("Select Genres", genre_options, default=['Action', 'Comedy', 'Sci-Fi'])

min_year = int(movies['year'].min())
max_year = int(movies['year'].max())
year_range = st.sidebar.slider("Select Year Range", min_year, max_year, (2000, 2014))

rating_range = st.sidebar.slider("Select Rating Range", 0.0, 5.0, (3.0, 5.0), 0.5)

# Filter Data
filtered_movies = movies[
    movies['genres'].apply(lambda x: any(g in x for g in selected_genres)) &
    movies['year'].between(year_range[0], year_range[1])
]

filtered_stats = movie_stats[
    movie_stats['movieId'].isin(filtered_movies['movieId']) &
    movie_stats['avg_rating'].between(rating_range[0], rating_range[1])
]

# Genre Treemap
filtered_genres = movies.explode('genres_list')
filtered_genres = filtered_genres[filtered_genres['genres_list'].isin(selected_genres)]
genre_counts = filtered_genres.groupby('genres_list').size().reset_index(name='count')

genre_treemap = px.treemap(
    genre_counts,
    path=['genres_list'],
    values='count',
    title=f'Genre Popularity ({year_range[0]} - {year_range[1]})',
    color_discrete_sequence=[colors['blue'], colors['orange'], colors['green']]
)
st.plotly_chart(genre_treemap, use_container_width=True)

# Rating Trend
yearly_filtered = ratings.merge(filtered_movies[['movieId', 'year']], on='movieId')
yearly_avg = yearly_filtered.groupby('year')['rating'].mean().reset_index()

rating_trend = px.line(
    yearly_avg,
    x='year',
    y='rating',
    title=f'Rating Trend ({", ".join(selected_genres)})',
    color_discrete_sequence=[colors['yellow']]
)
st.plotly_chart(rating_trend, use_container_width=True)

# Top Movies
top_movies = filtered_stats.sort_values(['avg_rating', 'rating_count'], ascending=[False, False]).head(20)

top_movies_scatter = px.scatter(
    top_movies,
    x='rating_count',
    y='avg_rating',
    hover_data=['title'],
    title='Top Rated Movies (Size = Rating Count)',
    size='rating_count',
    color='avg_rating',
    color_continuous_scale=[colors['background'], colors['blue']]
)
st.plotly_chart(top_movies_scatter, use_container_width=True)

# Tag Cloud
filtered_tags = tags[tags['movieId'].isin(filtered_movies['movieId'])]
tag_counts = filtered_tags['tag'].value_counts().head(50)

if not tag_counts.empty:
    wordcloud = WordCloud(width=800, height=400, background_color=colors['background'], colormap='viridis').generate_from_frequencies(tag_counts.to_dict())
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)
else:
    st.info("No tags available for the selected filters.")
