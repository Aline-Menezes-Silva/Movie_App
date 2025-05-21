import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
    st.error("Failed to read data files with tried encodings.")
    st.stop()

# Preprocessing
movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')
movies['genres_list'] = movies['genres'].str.split('|')

genre_popularity = movies.explode('genres_list') \
    .groupby('genres_list').size().reset_index(name='count') \
    .sort_values('count', ascending=False)

movie_stats = ratings.groupby('movieId').agg(
    avg_rating=('rating', 'mean'),
    rating_count=('rating', 'count'),
    rating_std=('rating', 'std')
).fillna(0)

tag_stats = tags.groupby('movieId').agg(
    tag_count=('tag', 'count'),
    unique_taggers=('userId', 'nunique')
).fillna(0)

movie_stats = movies.merge(movie_stats, on='movieId', how='left') \
                    .merge(tag_stats, on='movieId', how='left') \
                    .fillna(0)

# --- Streamlit Layout ---
st.set_page_config(page_title="FilmFilter Dashboard", layout="wide")
st.title("🎬 FilmFilter Dashboard")

with st.sidebar:
    st.header("📊 Filter Options")
    selected_genres = st.multiselect(
        "Select Genres:",
        options=genre_popularity['genres_list'].tolist(),
        default=["Action", "Comedy", "Sci-Fi"]
    )

    year_min = int(movies['year'].dropna().astype(int).min())
    year_max = int(movies['year'].dropna().astype(int).max())
    year_range = st.slider("Release Year Range:", year_min, year_max, (2000, 2014))

    rating_range = st.slider("Rating Range:", 0.0, 5.0, (3.0, 5.0), 0.5)

# --- Filtered Data ---
filtered_movies = movies[
    movies['genres'].apply(lambda x: any(genre in x for genre in selected_genres)) &
    movies['year'].fillna("0").astype(int).between(year_range[0], year_range[1])
]

filtered_stats = movie_stats[
    movie_stats['movieId'].isin(filtered_movies['movieId']) &
    movie_stats['avg_rating'].between(rating_range[0], rating_range[1])
]

# --- Genre Popularity Barplot ---
st.subheader("🎞️ Genre Popularity")

genre_counts = movies.explode('genres_list')
genre_counts = genre_counts[genre_counts['genres_list'].isin(selected_genres)]
genre_counts = genre_counts['genres_list'].value_counts().reset_index()
genre_counts.columns = ['Genre', 'Count']

fig1, ax1 = plt.subplots()
sns.barplot(x='Count', y='Genre', data=genre_counts, ax=ax1)
ax1.set_title("Popular Genres")
st.pyplot(fig1)

# --- Rating Trend Lineplot ---
st.subheader("📈 Rating Trends Over Years")

yearly = ratings.merge(filtered_movies[['movieId', 'year']], on='movieId')
yearly = yearly.dropna(subset=['year'])
yearly['year'] = yearly['year'].astype(int)
yearly_avg = yearly.groupby('year')['rating'].mean().reset_index()

fig2, ax2 = plt.subplots()
sns.lineplot(x='year', y='rating', data=yearly_avg, marker='o', ax=ax2)
ax2.set_title("Average Rating per Year")
ax2.set_xlabel("Year")
ax2.set_ylabel("Average Rating")
st.pyplot(fig2)

# --- Top Movies Scatter Plot ---
st.subheader("🏆 Top Rated Movies")

top_movies = filtered_stats.sort_values(['avg_rating', 'rating_count'], ascending=[False, False]).head(20)

fig3, ax3 = plt.subplots()
sns.scatterplot(data=top_movies, x='rating_count', y='avg_rating', size='rating_count', hue='avg_rating', ax=ax3, legend=False)
for i, row in top_movies.iterrows():
    ax3.text(row['rating_count'], row['avg_rating'], str(row['title'])[:25], fontsize=8)
ax3.set_title("Top Rated Movies")
ax3.set_xlabel("Rating Count")
ax3.set_ylabel("Average Rating")
st.pyplot(fig3)

# --- Tag Cloud / Tag Count Bar Plot ---
st.subheader("🏷️ Most Common Tags")

filtered_tags = tags[tags['movieId'].isin(filtered_movies['movieId'])]
top_tags = filtered_tags['tag'].value_counts().reset_index().head(20)
top_tags.columns = ['Tag', 'Count']

fig4, ax4 = plt.subplots()
sns.barplot(x='Count', y='Tag', data=top_tags, ax=ax4)
ax4.set_title("Top Tags by Users")
st.pyplot(fig4)
