import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config
st.set_page_config(
    page_title="FilmFilter Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Custom CSS
st.markdown(f"""
    <style>
        .main {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        .stSlider > div > div > div > div {{
            background-color: {colors['blue']};
        }}
        .stSelectbox > div > div > div {{
            color: #000000;
        }}
        .st-bb {{
            background-color: white;
        }}
        .st-at {{
            background-color: {colors['blue']};
        }}
        .css-1aumxhk {{
            background-color: {colors['background']};
            background-image: none;
        }}
    </style>
    """, unsafe_allow_html=True)

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
            
            # Data processing
            movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')
            movies['genres_list'] = movies['genres'].str.split('|')
            
            # Calculate genre popularity
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
            
            return movies, ratings, tags, movie_stats, genre_popularity
            
        except UnicodeDecodeError:
            continue
    else:
        st.error("None of the encodings worked for your files")
        st.stop()

movies, ratings, tags, movie_stats, genre_popularity = load_data()

# Sidebar filters
with st.sidebar:
    st.title("🎬 FilmFilter")
    st.markdown("Explore movie trends and patterns")
    
    # Info box
    with st.container():
        st.markdown("### Movie Insights")
        st.markdown("""
            - Popular genres
            - Rating trends
            - User tagging patterns
        """)
    
    st.markdown("---")
    
    # Genre Selector
    selected_genres = st.multiselect(
        "Select Genres:",
        options=genre_popularity['genres_list'].head(15),
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

# Filter data based on selections
filtered_movies = movies[
    movies['genres'].apply(lambda x: any(genre in x for genre in selected_genres)) &
    movies['year'].between(str(year_range[0]), str(year_range[1]))
]

filtered_stats = movie_stats[
    movie_stats['movieId'].isin(filtered_movies['movieId']) &
    movie_stats['avg_rating'].between(rating_range[0], rating_range[1])
]

# Main content
st.title("FilmFilter Dashboard")

# First row of charts
col1, col2 = st.columns(2)

with col1:
    # Genre Treemap
    filtered_genres = movies.explode('genres_list')
    filtered_genres = filtered_genres[filtered_genres['genres_list'].isin(selected_genres)]
    genre_counts = filtered_genres.groupby('genres_list').size().reset_index(name='count')
    
    fig_treemap = px.treemap(
        genre_counts,
        path=['genres_list'],
        values='count',
        title=f'Genre Popularity ({year_range[0]}-{year_range[1]})',
        color_discrete_sequence=[colors['blue'], colors['orange'], colors['green']]
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

with col2:
    # Rating Trend
    yearly_filtered = ratings.merge(filtered_movies[['movieId', 'year']], on='movieId')
    yearly_avg = yearly_filtered.groupby('year')['rating'].mean().reset_index()
    
    fig_trend = px.line(
        yearly_avg,
        x='year',
        y='rating',
        title=f'Rating Trend ({", ".join(selected_genres)})',
        color_discrete_sequence=[colors['yellow']]
    )
    fig_trend.update_layout(plot_bgcolor=colors['background'])
    st.plotly_chart(fig_trend, use_container_width=True)

# Second row - Top Movies
st.subheader("Top Rated Movies")
top_movies = filtered_stats.sort_values(['avg_rating', 'rating_count'], ascending=[False, False]).head(20)

fig_movies = px.scatter(
    top_movies,
    x='rating_count',
    y='avg_rating',
    hover_data=['title'],
    title='Top Rated Movies (Size = Rating Count)',
    size='rating_count',
    color='avg_rating',
    color_continuous_scale=[colors['background'], colors['blue']]
)
fig_movies.update_layout(
    xaxis_title="Number of Ratings",
    yaxis_title="Average Rating",
    hovermode='closest'
)
st.plotly_chart(fig_movies, use_container_width=True)

# Third row - Tag Cloud
st.subheader("Popular User Tags")
filtered_tags = tags[tags['movieId'].isin(filtered_movies['movieId'])]
tag_counts = filtered_tags['tag'].value_counts().reset_index().head(20)
tag_counts.columns = ['tag', 'count']

fig_tags = px.bar(
    tag_counts,
    x='count',
    y='tag',
    orientation='h',
    title='Popular User Tags',
    color_discrete_sequence=[colors['blue1']]
)
fig_tags.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_tags, use_container_width=True)