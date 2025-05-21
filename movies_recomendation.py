import pandas as pd
import numpy as np
import streamlit as st

# Define color scheme
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

# Load datasets
@st.cache_data
def load_data():
    encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings_to_try:
        try:
            movies = pd.read_csv("movies.csv", encoding=encoding)
            ratings = pd.read_csv('rating.csv', encoding=encoding)
            tags = pd.read_csv('tags.csv', encoding=encoding)
            st.success(f"Successfully loaded with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
    else:
        st.error("None of the encodings worked for your files")
        return None, None, None
    
    # Extract Year from Movie Title
    movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')
    
    # Split Genres into List
    movies['genres_list'] = movies['genres'].str.split('|')
    
    return movies, ratings, tags

movies, ratings, tags = load_data()

if movies is not None:
    # Calculate Genre Popularity
    genre_popularity = movies.explode('genres_list').groupby('genres_list').size().reset_index(name='count')
    genre_popularity = genre_popularity.sort_values('count', ascending=False)
    
    # Create rating statistics 
    movie_stats = ratings.groupby('movieId').agg(
        avg_rating=('rating', 'mean'),
        rating_count=('rating', 'count'),
        rating_std=('rating', 'std')
    ).fillna(0)
    
    # Create tag statistics 
    tag_stats = tags.groupby('movieId').agg(
        tag_count=('tag', 'count'),
        unique_taggers=('userId', 'nunique')
    ).fillna(0)
    
    # Merge all features
    movie_stats = movies.merge(movie_stats, on='movieId', how='left')\
                      .merge(tag_stats, on='movieId', how='left')\
                      .fillna(0)
    
    # Streamlit app layout
    st.set_page_config(layout="wide")
    
    # Custom CSS for styling
    st.markdown(
        f"""
        <style>
        .reportview-container {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        .sidebar .sidebar-content {{
            background-color: {colors['background']};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {colors['text']};
        }}
        .stSelectbox, .stSlider, .stMultiSelect {{
            color: #000000;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Header
    st.title("FilmFilter Dashboard")
    
    # Sidebar with filters
    with st.sidebar:
        st.markdown("### Filter Options")
        
        # Genre Selector
        selected_genres = st.multiselect(
            "Select Genres:",
            options=genre_popularity['genres_list'].head(15).tolist(),
            default=['Action', 'Comedy', 'Sci-Fi']
        )
        
        # Year Slider
        min_year = int(movies['year'].min())
        max_year = int(movies['year'].max())
        year_range = st.slider(
            "Release Year Range:",
            min_value=min_year,
            max_value=max_year,
            value=(2000, 2014),
            step=1
        )
        
        # Rating Slider
        rating_range = st.slider(
            "Rating Range:",
            min_value=0.0,
            max_value=5.0,
            value=(3.0, 5.0),
            step=0.5
        )
    
    # Main content
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Info card
        st.markdown(
            f"""
            <div style="
                background-color: {colors['background']};
                color: {colors['text']};
                border: 2px solid {colors['text']};
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            ">
                <h4 style="color: {colors['gold']};">Movie Insights</h4>
                <p>Explore movie trends and patterns:</p>
                <ul>
                    <li>Popular genres</li>
                    <li>Rating trends</li>
                    <li>User tagging patterns</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        # Filter movies based on selections
        filtered_movies = movies[
            movies['genres'].apply(lambda x: any(genre in x for genre in selected_genres)) &
            movies['year'].between(str(year_range[0]), str(year_range[1]))
        ]
        
        # Merge with ratings
        filtered_stats = movie_stats[
            movie_stats['movieId'].isin(filtered_movies['movieId']) &
            movie_stats['avg_rating'].between(rating_range[0], rating_range[1])
        ]
        
        # Display visualizations in tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Genre Popularity", 
            "Rating Trend", 
            "Top Movies", 
            "Tag Cloud"
        ])
        
        with tab1:
            # Genre treemap
            filtered_genres = movies.explode('genres_list')
            filtered_genres = filtered_genres[filtered_genres['genres_list'].isin(selected_genres)]
            genre_counts = filtered_genres.groupby('genres_list').size().reset_index(name='count')
            
            st.bar_chart(
                genre_counts.set_index('genres_list'),
                use_container_width=True
            )
            st.caption(f"Genre Popularity ({year_range[0]}-{year_range[1]})")
        
        with tab2:
            # Rating trend
            yearly_filtered = ratings.merge(filtered_movies[['movieId', 'year']], on='movieId')
            yearly_avg = yearly_filtered.groupby('year')['rating'].mean().reset_index()
            
            st.line_chart(
                yearly_avg.set_index('year'),
                use_container_width=True
            )
            st.caption(f"Rating Trend ({', '.join(selected_genres)})")
        
        with tab3:
            # Top movies
            top_movies = filtered_stats.sort_values(['avg_rating', 'rating_count'], ascending=[False, False]).head(20)
            
            st.dataframe(
                top_movies[['title', 'avg_rating', 'rating_count']].rename(columns={
                    'title': 'Movie Title',
                    'avg_rating': 'Average Rating',
                    'rating_count': 'Number of Ratings'
                }),
                use_container_width=True,
                hide_index=True
            )
            st.caption("Top Rated Movies")
        
        with tab4:
            # Tag cloud
            filtered_tags = tags[tags['movieId'].isin(filtered_movies['movieId'])]
            tag_counts = filtered_tags['tag'].value_counts().reset_index().head(20)
            tag_counts.columns = ['tag', 'count']
            
            st.bar_chart(
                tag_counts.set_index('tag'),
                use_container_width=True
            )
            st.caption("Popular User Tags")