"""
Admin configuration for Movies app
"""

from django.contrib import admin
from .models import Genre, Movie, MovieReview


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Admin for Genre"""
    list_display = ['name', 'movie_count']
    search_fields = ['name']
    
    def movie_count(self, obj):
        """Display number of movies in this genre"""
        return obj.movies.count()
    movie_count.short_description = 'Movies'


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """Admin for Movie"""
    list_display = ['title', 'release_date', 'status', 'rating', 'is_featured', 'language']
    search_fields = ['title', 'director']
    list_filter = ['status', 'language', 'certification', 'is_featured', 'release_date']
    filter_horizontal = ['genres']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'poster', 'banner')
        }),
        ('Details', {
            'fields': ('release_date', 'duration_minutes', 'language', 'genres', 'certification')
        }),
        ('Credits', {
            'fields': ('director', 'cast', 'rating')
        }),
        ('Status', {
            'fields': ('status', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MovieReview)
class MovieReviewAdmin(admin.ModelAdmin):
    """Admin for MovieReview"""
    list_display = ['movie', 'user', 'rating', 'is_verified_purchase', 'created_at']
    search_fields = ['movie__title', 'user__username']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
