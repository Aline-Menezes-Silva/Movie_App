import streamlit as st
import pandas as pd
import numpy as np

# Set page config
st.set_page_config(layout="wide", page_title="Movie Analysis Dashboard")

# Color scheme
colors = {
    'background': '#1E3A5F',
    'text': '#f8f9fa',
    'green': '#00AA55',
    'orange': '#FF6B00',
    'gold': '#FFC233',
    'blue': '#3A7BFF',
    'yellow': '#FFD700'
}

# Custom CSS
st.markdown(f"""
    <style>
        .main {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        .stSlider > div > div > div > div {{
            background: {colors['gold']} !important;
        }}
        .st-bb {{
            background-color: transparent;
        }}
        .st-at {{
            background-color: {colors['blue']};
        }}
        div[data-baseweb="select"] > div {{
            background-color: transparent !important;
            color: {colors['text']} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("🎬 FilmFilter Dashboard")

# Load data with robust encoding handling
@st.cache_data
def load_data():
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open("movies.csv", 'rb') as f:
                movies_content = f.read().decode(encoding)
            movies = pd.read_csv(io.StringIO(movies_content))
            
            with open("rating.csv", 'rb') as f:
                ratings_content = f.read().decode(encoding)
            ratings = pd.read_csv(io.StringIO(ratings_content))
            
            with open("tags.csv", 'rb') as f:
                tags_content = f.read().decode(encoding)
            tags = pd.read_csv(io.StringIO(tags_content))
            
            st.success(f"Successfully loaded with {encoding} encoding")
            break
        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            continue
    else:
        st.error("Failed to load CSV files with all attempted encodings")
        return None, None, None
    
    # Data processing
    movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')
    movies['genres_list'] = movies['genres'].str.split('|')
    
    movie_stats = ratings.groupby('movieId').agg(
        avg_rating=('rating', 'mean'),
        rating_count=('rating', 'count'),
        rating_std=('rating', 'std')
    ).fillna(0)
    
    tag_stats = tags.groupby('movieId').agg(
        tag_count=('tag', 'count'),
        unique_taggers=('userId', 'nunique')
    ).fillna(0)
    
    return movies.merge(movie_stats, on='movieId', how='left').merge(tag_stats, on='movieId', how='left').fillna(0), movies, tags

movie_stats, movies, tags = load_data()

if movie_stats is None:
    st.error("Critical error: Could not load data. Please check your CSV files.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("🎛️ Filters")
    
    # Genre selector
    genre_popularity = movies.explode('genres_list').groupby('genres_list').size().reset_index(name='count')
    selected_genres = st.multiselect(
        "Select genres",
        options=genre_popularity['genres_list'].unique(),
        default=['Action', 'Comedy', 'Drama'],
        key="genre_select"
    )
    
    # Year slider
    year_range = st.slider(
        "Release year range",
        min_value=int(movies['year'].min()),
        max_value=int(movies['year'].max()),
        value=(2000, 2014),
        key="year_slider"
    )
    
    # Rating slider
    rating_range = st.slider(
        "Rating range",
        min_value=0.0,
        max_value=5.0,
        value=(3.0, 5.0),
        step=0.5,
        key="rating_slider"
    )

# Filter data
filtered_movies = movies[
    movies['genres'].apply(lambda x: any(genre in x for genre in selected_genres)) &
    movies['year'].between(str(year_range[0]), str(year_range[1]))
]

filtered_stats = movie_stats[
    movie_stats['movieId'].isin(filtered_movies['movieId']) &
    movie_stats['avg_rating'].between(rating_range[0], rating_range[1])
]

# Main dashboard
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 📊 Genre Popularity")
    genre_counts = movies.explode('genres_list')
    genre_counts = genre_counts[genre_counts['genres_list'].isin(selected_genres)]
    genre_counts = genre_counts.groupby('genres_list').size().reset_index(name='count')
    
    fig = px.treemap(
        genre_counts,
        path=['genres_list'],
        values='count',
        color_discrete_sequence=[colors['blue'], colors['orange'], colors['green']]
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 📈 Rating Trends")
    yearly_filtered = ratings.merge(filtered_movies[['movieId', 'year']], on='movieId')
    yearly_avg = yearly_filtered.groupby('year')['rating'].mean().reset_index()
    
    fig = px.line(
        yearly_avg,
        x='year',
        y='rating',
        color_discrete_sequence=[colors['yellow']]
    )
    st.plotly_chart(fig, use_container_width=True)

# Second row
st.markdown("### 🏆 Top Rated Movies")
top_movies = filtered_stats.sort_values(['avg_rating', 'rating_count'], ascending=[False, False]).head(20)
fig = px.scatter(
    top_movies,
    x='rating_count',
    y='avg_rating',
    hover_data=['title'],
    size='rating_count',
    color='avg_rating',
    color_continuous_scale=[colors['background'], colors['blue']]
)
st.plotly_chart(fig, use_container_width=True)

# Tag cloud
st.markdown("### 🏷️ Popular Tags")
filtered_tags = tags[tags['movieId'].isin(filtered_movies['movieId'])]
tag_counts = filtered_tags['tag'].value_counts().reset_index().head(20)
tag_counts.columns = ['tag', 'count']

fig = px.bar(
    tag_counts,
    x='count',
    y='tag',
    orientation='h',
    color_discrete_sequence=[colors['blue']]
)
st.plotly_chart(fig, use_container_width=True)