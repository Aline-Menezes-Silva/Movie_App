import streamlit as st
import pandas as pd
import plotly.express as px

# Load datasets with fallback encoding
encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
for encoding in encodings_to_try:
    try:
        movies = pd.read_csv("movies.csv", encoding=encoding)
        ratings = pd.read_csv("rating.csv", encoding=encoding)
        tags = pd.read_csv("tags.csv", encoding=encoding)
        break
    except UnicodeDecodeError:
        continue
else:
    st.error("None of the encodings worked for your files.")
    st.stop()

# Extract year from title
movies['year'] = movies['title'].str.extract(r'\((\d{4})\)').astype(str)

# Split genres into list
movies['genres_list'] = movies['genres'].str.split('|')

# Genre popularity
genre_popularity = movies.explode('genres_list').groupby('genres_list').size().reset_index(name='count')
genre_popularity = genre_popularity.sort_values('count', ascending=False)

# Rating stats
movie_stats = ratings.groupby('movieId').agg(
    avg_rating=('rating', 'mean'),
    rating_count=('rating', 'count'),
    rating_std=('rating', 'std')
).fillna(0)

# Tag stats
tag_stats = tags.groupby('movieId').agg(
    tag_count=('tag', 'count'),
    unique_taggers=('userId', 'nunique')
).fillna(0)

# Merge all
movie_stats = movies.merge(movie_stats, on='movieId', how='left')\
                    .merge(tag_stats, on='movieId', how='left')\
                    .fillna(0)

# --- Streamlit UI ---
st.set_page_config(page_title="FilmFilter Dashboard", layout="wide")
st.title("🎬 FilmFilter Dashboard")

with st.sidebar:
    st.header("📊 Filter Options")

    selected_genres = st.multiselect(
        "Select Genres:",
        options=genre_popularity['genres_list'].tolist(),
        default=["Action", "Comedy", "Sci-Fi"]
    )

    year_min = int(movies['year'].replace("nan", "0").astype(int).min())
    year_max = int(movies['year'].replace("nan", "0").astype(int).max())
    year_range = st.slider("Select Year Range:", min_value=year_min, max_value=year_max, value=(2000, 2014))

    rating_range = st.slider("Select Rating Range:", 0.0, 5.0, (3.0, 5.0), 0.5)

# --- Filtering Data ---
filtered_movies = movies[
    movies['genres'].apply(lambda x: any(genre in x for genre in selected_genres)) &
    movies['year'].astype(str).between(str(year_range[0]), str(year_range[1]))
]

filtered_stats = movie_stats[
    movie_stats['movieId'].isin(filtered_movies['movieId']) &
    movie_stats['avg_rating'].between(rating_range[0], rating_range[1])
]

# --- Genre Treemap ---
filtered_genres = movies.explode('genres_list')
filtered_genres = filtered_genres[filtered_genres['genres_list'].isin(selected_genres)]
genre_counts = filtered_genres.groupby('genres_list').size().reset_index(name='count')

genre_treemap = px.treemap(
    genre_counts,
    path=['genres_list'],
    values='count',
    title=f'Genre Popularity ({year_range[0]} - {year_range[1]})'
)
st.plotly_chart(genre_treemap, use_container_width=True)

# --- Rating Trend ---
yearly_filtered = ratings.merge(filtered_movies[['movieId', 'year']], on='movieId')
yearly_avg = yearly_filtered.groupby('year')['rating'].mean().reset_index()

rating_trend = px.line(
    yearly_avg,
    x='year',
    y='rating',
    title=f'Rating Trend ({", ".join(selected_genres)})'
)
st.plotly_chart(rating_trend, use_container_width=True)

# --- Top Rated Movies ---
top_movies = filtered_stats.sort_values(['avg_rating', 'rating_count'], ascending=[False, False]).head(20)

top_movies_scatter = px.scatter(
    top_movies,
    x='rating_count',
    y='avg_rating',
    size='rating_count',
    hover_data=['title'],
    color='avg_rating',
    title='Top Rated Movies (Size = Rating Count)',
    color_continuous_scale='Blues'
)
st.plotly_chart(top_movies_scatter, use_container_width=True)

# --- Tag Cloud (Bar Plot) ---
filtered_tags = tags[tags['movieId'].isin(filtered_movies['movieId'])]
tag_counts = filtered_tags['tag'].value_counts().reset_index().head(20)
tag_counts.columns = ['tag', 'count']

tag_chart = px.bar(
    tag_counts,
    x='count',
    y='tag',
    orientation='h',
    title='Popular User Tags'
)
tag_chart.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(tag_chart, use_container_width=True)
