"""
URL configuration for Movies app
"""

from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    # Movie listing and details
    path('', views.movie_list, name='movie_list'),
    path('<int:pk>/', views.movie_detail, name='movie_detail'),
    path('<int:pk>/review/', views.submit_review, name='submit_review'),
    
    # Coming soon movies
    path('coming-soon/', views.coming_soon_movies, name='coming_soon'),
    # Add movie (admin / theatre manager)
    path('add/', views.add_movie, name='add_movie'),
    
    # Genres
    path('genres/', views.genre_list, name='genre_list'),
    path('genre/<int:genre_id>/', views.movies_by_genre, name='movies_by_genre'),
]
