#!/usr/bin/env python
# coding: utf-8

# ### Interactive Movie Recommendation Dashboard for Young Adults (18-35)
# 
# - " When designing charts and dashboards for people aged 18 to 35, it's important to consider modern aesthetics, readability, accessibility and emotional impact. This age group tends to prefer clean, vibrant and engaging color schemes."
# 
# https://www.urban.org/sites/default/files/2022-12/Do%20No%20Harm%20Guide%20Centering%20Accessibility%20in%20Data%20Visualization.pdf

# In[1]:


#!pip install dash-bootstrap-components


# In[2]:


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import base64


# In[3]:


#!pip install --upgrade plotly


# In[4]:


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


# In[5]:


movies


# In[6]:


movies.info()


# In[7]:


movies.describe(include = "object")


# In[8]:


print(f"\nUnique genres: {movies['genres'].str.split('|').explode().nunique()}")


# In[9]:


ratings


# In[10]:


ratings.info()


# In[11]:


print(f"\nUnique users: {ratings['userId'].nunique()}")
print(f"Rating distribution:\n{ratings['rating'].value_counts(normalize=True)}")


# In[12]:


tags


# In[13]:


tags.info()


# In[14]:


print(tags['tag'].value_counts().head(20))


# ## Step 1: Pre-processing and merge the datasets 

# ####  Extract year from movie title and the release year from movie titles. 
# 
# - Many movie titles include the release year in parentheses. The year will be separated into its own column for easier analysis.

# In[15]:


# Extract Year from Movie Title

movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')


# #### Split genres into list separates 
# 
# - The Films in the dataset belong to more than one genre. By separating them into a list, each genero can be analysed in more detail.

# In[16]:


#Split Genres into List

movies['genres_list'] = movies['genres'].str.split('|')


# #### Calculate genre popularity counts how many movies belong to each genre. 
# 
# - To be able to understand which genres are most common in the dataset

# In[17]:


#Calculate Genre Popularity

genre_popularity = movies.explode('genres_list').groupby('genres_list').size().reset_index(name='count')
genre_popularity = genre_popularity.sort_values('count', ascending=False)


# #### Create rating statistics 
# 
# - Calculates average rating and number of ratings per movie, to analyse movies peformance. 

# In[18]:


# Create rating statistics 

movie_stats = ratings.groupby('movieId').agg(
    avg_rating=('rating', 'mean'),
    rating_count=('rating', 'count'),
    rating_std=('rating', 'std')
).fillna(0)


# #### Create tag statistics 
# 
# Calculates tag rating and number of tag per movie, to measure audience engagement. 

# In[19]:


#  Create tag statistics 

tag_stats = tags.groupby('movieId').agg(
    tag_count=('tag', 'count'),
    unique_taggers=('userId', 'nunique')
).fillna(0)


# #### Merge the datasets
# 
# To create a unified dataset for the dashboard, where each movie has:
# 
# - title, year and genres.
# 
# - Rating statistics (avg rating, count, std).
# 
# - Tag statistics (tag count, unique taggers).
# 
# The fillna(0) ensures missing values are treated as zeros.

# In[20]:


# Merge all features

movie_stats = movies.merge(movie_stats, on='movieId', how='left')\
                      .merge(tag_stats, on='movieId', how='left')\
                      .fillna(0)


# In[21]:


movie_stats


# In[22]:


movie_stats.info()


# ### Dashboard Planning
# 
# To create a useful dashboard, I will focus on four key areas:
# 
# - Popularity Metrics = Track the most-rated films and the highest-rated films. Identify the most active users who leave the most reviews.
# 
# - Genre Analysis = Look at how films are distributed across different genres. Checking how genre popularity changes over time. ALso compare average ratings by genre to see which ones perform best.
# 
# - Temporal Trends = Analyse how rating activity varies over time.
# 
# - Tag Analysis = Find the most frequently used tags on films. Group related tags into clusters for better insights.

# ## Step 2: Preparing to build the dashboard 
# 

# - Instead of manually styling the dashboard, using a Bootstrap (COSMO) theme ensures a visually appealing and cohesive design:

# In[23]:


# Initialise the Dashboard with bootstrap theme

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])


#  

# ##### Defining color scheme for the dashboard .
# 
# The background will be used a soft navy blue, it is an eye-friendly background. This shade is easy on the eyes for prolonged use, reducing strain. Creates a calm, professional, yet modern feel, avoiding harsh blacks or bright whites. 
# 
# For text I will be using a Soft white (95% lightness), it makes high contrast against the dark background for readability, but not pure white to avoid glare.
# 
# The accent Colors are bright and playful, yet balanced. they are vibrant but not overwhelming, fitting a young audience while maintaining usability:
# 
# 
# gold: Golden-yellow for importsnt subtitles. Used for highlights premium features eye-catching but not harsh.
# 
# blue and Soft blues:  for interactive elements (buttons) and some chart. 
# 
# yellow: bright but soft yellow for trendy.
# 
# I am also applying a triadic in the treemap  – 3 colors that are equidistance apart on the color wheel: Soft bright blue, Soft bright green and Soft bright red. This option balances colors well and gives lots of contrast and variety. It can make visually interesting and dynamic layouts by using the natural vibrancy and balance of triadic color combinations.It is also good for showing important information and making things interesting to look at and can make lively designs that grab users’ attention.
# https://freshbi.com/blogs/color-theory-in-dashboard-design/
# 
# 
# Young adults like vibrant, lively colours, but the palette avoids neon shades to keep things clean and not overwhelming. The combination of cool tones (like navy and blue) with warm ones (such as orange, gold, and pink) keeps the design fresh and balanced. Soft contrasts help prevent eye strain, which is especially important for dashboards used for long periods. Bright pops of colour highlight important data, while strong text-background contrast ensures easy reading.
# 

# In[24]:


# Define color scheme for young adult demographic

colors = {
    'background': '#1E3A5F ',  
    'text': '#f8f9fa',      


    'green': '#00AA55',     
    'orange': '#FF6B00',  
    'gold': '#FFC233',   
    'blue': '#3A7BFF',
    'yellow': '#FFD700',
    'blue1': '#5A7BDE'

}


#  

# - An information box (called "card") will be created to help understand what can be done with the dashboard. It uses simple styling to make the box look nice, with a background colour, text colour, and border. Inside the box, there's a title ("Movie Insights") and a list explaining that users can explore: 1) which genres are popular, 2) how ratings change over time, and 3) what tags users commonly add to movies. The purpose is to give users a clear guide about the dashboard's features before start exploring the data. 
# 

# In[25]:


# Make an info box

def make_info_card():
    card_style = {
        'background': colors['bg'],
        'color': colors['text'],
        'border': f"2px solid {colors['second']}"
    }

    return dbc.Card(
        dbc.CardBody([
            html.H4("Movie Insights"),
            html.P("Explore movie trends and patterns:"),
            html.Ul([
                html.Li("Popular genres"),
                html.Li("Rating trends"),
                html.Li("User tags")
            ])
        ]),
        style=card_style
    )



# In[26]:


def create_info_card():
    return dbc.Card(
        dbc.CardBody([
            html.H4(
                "Movie Insights", 
                className="card-title",
                style={'color': colors['gold']}  
            ),
            html.P("Explore movie trends and patterns:", className="card-text"),
            html.Ul([
                html.Li("Popular genres"),
                html.Li("Rating trends"),
                html.Li("User tagging patterns")
            ])
        ]),
        style={
            'background-color': colors['background'],
            'color': colors['text'], 
            'border': f"2px solid {colors['text']}"
        }
    )


#  

# ### Step 3: Building the Layout of the Dashboard
# 

# Next step is to create the layout for the Dashboard using Dash Bootstrap Components (DBC). It sets up a clean, organised interface with:
# 
# - A header showing the dashboard title in bold text. 
# - A left sidebar with interactive filters (genre dropdown, year slider and rating slider) so users can customise which movies are displayed.
# 
# A main content area with four visualisations:
# 
# - Genre treemap (shows popular genres)
# - Rating trend line chart (displays how ratings change over time)
# - Top movies scatter plot (highlights highly-rated films)
# - Tag cloud (reveals common user tags)
# 
# The layout uses responsive design (adjusts to screen size) and a colour scheme for better readability. The filters help users narrow down data, while the graphs update dynamically to show insights based on their selections. This makes it easy to explore movie trends.

# In[27]:


app.layout = dbc.Container(
    [
        # Header with title and age group indicator

        dbc.Row(
            dbc.Col(
                html.H1(
                    "FilmFilter Dashboard", 
                    style={
                        'color': colors['text'],
                        'textAlign': 'center',

                        'font-weight': 'bold'
                    }
                ), 
                width=12
            )
        ),


        # Main content rows
        dbc.Row(
            [
                # Left column - info and filters
                dbc.Col(
                    [
                        create_info_card(),
                        html.Br(),
                        html.H4("Filter Options", style={
                            'color': colors['gold'], 
                            'margin-bottom': '15px',
                            'margin-top': '10px'
                        }),

                        # Genre Selector
                        html.Div("Select Genres:", style={
                            'color': colors['text'], 
                            'margin-bottom': '5px',
                            'font-weight': 'bold'
                        }),
                        dcc.Dropdown(
                            id='genre-selector',
                            options=[{'label': genre, 'value': genre} 
                                    for genre in genre_popularity['genres_list'].head(15)],
                            value=['Action', 'Comedy', 'Sci-Fi'],
                            multi=True,
                            style={'color': '#000000'}
                        ),
                        html.Br(),

                        # Year Slider
                        html.Div([
                            html.Div("Release Year Range:", style={
                                'color': colors['text'], 
                                'margin-bottom': '5px',
                                'font-weight': 'bold'
                            }),
                            html.Div(f"{int(movies['year'].min())} to {int(movies['year'].max())}", 
                                style={
                                    'color': colors['text'],
                                    'font-size': '0.8em',
                                    'margin-bottom': '5px'
                                }),
                            dcc.RangeSlider(
                                id='year-slider',
                                min=int(movies['year'].min()),
                                max=int(movies['year'].max()),
                                step=1,
                                value=[2000, 2014],
                                marks={
                                    str(int(movies['year'].min())): {'label': str(int(movies['year'].min())), 
                                    'style': {'margin-top': '15px'}},
                                    str(int(movies['year'].max())): {'label': str(int(movies['year'].max())), 
                                    'style': {'margin-top': '15px'}}
                                },
                                tooltip={"placement": "bottom", "always_visible": True},
                                allowCross=False
                            )
                        ], style={'margin-bottom': '30px'}),

                        # Rating Slider
                        html.Div([
                            html.Div("Rating Range:", style={
                                'color': colors['text'], 
                                'margin-bottom': '5px',
                                'font-weight': 'bold'
                            }),
                            dcc.RangeSlider(
                                id='rating-slider',
                                min=0,
                                max=5,
                                step=0.5,
                                value=[3, 5],
                                marks={
                                    0: {'label': '0', 'style': {'margin-top': '15px'}},
                                    5: {'label': '5', 'style': {'margin-top': '15px'}}
                                },
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], style={'margin-bottom': '20px'}),
                    ],
                    width=3,
                    style={
                        'padding-right': '30px', 
                        'padding-left': '15px',
                        'padding-top': '10px'
                    }
                ),

                # Right column - visualisations
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(id='genre-treemap'), 
                                width=6
                                ),
                                dbc.Col(dcc.Graph(id='rating-trend'), 
                                width=6
                                )
                            ],
                            style={'margin-bottom': '20px'}
                        ),
                        dbc.Row(
                            dbc.Col(
                                dcc.Graph(id='top-movies'), 
                                width=12
                            ),
                            style={'margin-bottom': '20px'}
                        ),
                        dbc.Row(
                            dbc.Col(
                                dcc.Graph(id='tag-cloud'), 
                                width=12
                            )
                        )
                    ],
                    width=9,
                    style={'padding-top': '10px'}
                )
            ],
            style={'margin-top': '10px'}
        )
    ], 
    fluid=True, 
    style={
        'backgroundColor': colors['background'],
        'padding': '15px'
    }
)


#  

# ### Step 4: Adding Interactivity to the Dashboard
# 
# - This next step updates the movie dashboard when users change their selections. It takes the chosen genres, years and rating range, then filters the movie data to match. The dashboard shows four things: 
# 
# 1) a treemap displaying which genres are most common, 
# 2) a line graph showing how ratings have changed over time, 
# 3) a scatter plot of the highest-rated movies (where bigger dots mean more ratings), 
# 4) a horizontal bar chart of popular tags. Each chart updates automatically when users adjust the filters, helping them explore movie trends visually. 
# 
# - The code ensures all charts work together, showing only relevant data based on the user's current choices.

# In[28]:


@app.callback(
    [Output('genre-treemap', 'figure'),
     Output('rating-trend', 'figure'),
     Output('top-movies', 'figure'),
     Output('tag-cloud', 'figure')],
    [Input('genre-selector', 'value'),
     Input('year-slider', 'value'),
     Input('rating-slider', 'value')]
)
def update_dashboard(selected_genres, year_range, rating_range):
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

    # Update genre treemap
    filtered_genres = movies.explode('genres_list')
    filtered_genres = filtered_genres[filtered_genres['genres_list'].isin(selected_genres)]
    genre_counts = filtered_genres.groupby('genres_list').size().reset_index(name='count')

    genre_treemap = px.treemap(
        genre_counts,
        path=['genres_list'],
        values='count',
        title=f'Genre Popularity ({year_range[0]}-{year_range[1]})',
        color_discrete_sequence=[colors['blue'], colors['orange'], colors['green']]
    )

    # Update rating trend
    yearly_filtered = ratings.merge(filtered_movies[['movieId', 'year']], on='movieId')
    yearly_avg = yearly_filtered.groupby('year')['rating'].mean().reset_index()

    rating_trend = px.line(
        yearly_avg,
        x='year',
        y='rating',
        title=f'Rating Trend ({", ".join(selected_genres)})',
        color_discrete_sequence=[colors['yellow']]
    )
    rating_trend.update_layout(plot_bgcolor=colors['background'])

    # Update top movies scatter plot
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
    top_movies_scatter.update_layout(
        xaxis_title="Number of Ratings",
        yaxis_title="Average Rating",
        hovermode='closest'
    )

    # Update tag cloud 
    filtered_tags = tags[tags['movieId'].isin(filtered_movies['movieId'])]
    tag_counts = filtered_tags['tag'].value_counts().reset_index().head(20)
    tag_counts.columns = ['tag', 'count']

    tag_chart = px.bar(
        tag_counts,
        x='count',
        y='tag',
        orientation='h',
        title='Popular User Tags',
        color_discrete_sequence=[colors['blue1']]
    )
    tag_chart.update_layout(yaxis={'categoryorder':'total ascending'})

    return genre_treemap, rating_trend, top_movies_scatter, tag_chart


# ### Step 5: Running the Dashboard

# In[29]:


if __name__ == '__main__':
    app.run(debug=True, port=8051)


# ### Machine Learning Suitability:
# 
# - Rich Feature Space: Genres, Ratings and Tags Offer Multiple Ways to Recommend Films
# The dataset includes different types of information that help recommendation systems work better. Together, these features help the system suggest films in different ways, making recommendations more accurate and varied.
# 
# - User Behaviour Data: Ratings Help Suggest Films Based on What Others Enjoyed
# By looking at how users rate films, the system can find patterns. For example, if many people who liked Toy Story also enjoyed Finding Nemo, the system can recommend similar films to new users. This method, called collaborative filtering, works well because it relies on real user preferences rather than just film descriptions.
# 
# - Content Metadata: Genres Help Recommend Similar Films
# Since each film has genre information, the system can suggest films with the same or similar genres. If a user watches lots of horror films, the system will recommend more horrors. This is called content-based filtering, and it’s useful when there isn’t much user rating data available.
# 
# - Temporal Patterns: Release Years Help Recommend Recent or Classic Films
# The dataset includes the year each film was released, which helps the system adjust recommendations based on time. Some users might prefer newer films, while others enjoy classics. By checking the release year, the system can suggest films that match the user’s preference for recent or older movies, making recommendations more personalised.
# 
# 

# In[ ]:




