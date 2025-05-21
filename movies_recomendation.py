import streamlit as st

import pandas as pd

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


# Extract Year from Movie Title

movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')

#Split Genres into List

movies['genres_list'] = movies['genres'].str.split('|')


#Calculate Genre Popularity

genre_popularity = movies.explode('genres_list').groupby('genres_list').size().reset_index(name='count')
genre_popularity = genre_popularity.sort_values('count', ascending=False)

# Create rating statistics 

movie_stats = ratings.groupby('movieId').agg(
    avg_rating=('rating', 'mean'),
    rating_count=('rating', 'count'),
    rating_std=('rating', 'std')
).fillna(0)


#  Create tag statistics 

tag_stats = tags.groupby('movieId').agg(
    tag_count=('tag', 'count'),
    unique_taggers=('userId', 'nunique')
).fillna(0)

# Merge all features

movie_stats = movies.merge(movie_stats, on='movieId', how='left')\
                      .merge(tag_stats, on='movieId', how='left')\
                      .fillna(0)


# Initialise the Dashboard with bootstrap theme

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])


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

if __name__ == '__main__':
    app.run(debug=True, port=8051)