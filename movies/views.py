"""
Views for Movies app
- Display movies list with search/filter
- Movie details page with reviews
- Submit and view reviews
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Movie, Genre, MovieReview
from .forms import MovieSearchForm, MovieReviewForm, MovieForm


def movie_list(request):
    """
    Display list of all movies with search and filter functionality
    """
    movies = Movie.objects.filter(status='running').prefetch_related('genres')
    form = MovieSearchForm(request.GET or None)
    
    # Search by title or director
    if request.GET.get('query'):
        query = request.GET.get('query')
        movies = movies.filter(
            Q(title__icontains=query) | 
            Q(director__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Filter by language
    if request.GET.get('language'):
        movies = movies.filter(language=request.GET.get('language'))
    
    # Filter by certification
    if request.GET.get('certification'):
        movies = movies.filter(certification=request.GET.get('certification'))
    
    # Filter by genre
    if request.GET.get('genre'):
        genre_name = request.GET.get('genre')
        movies = movies.filter(genres__name__icontains=genre_name)
    
    # Annotate with review count and average rating
    movies = movies.annotate(
        review_count=Count('reviews'),
        average_rating=Avg('reviews__rating')
    )
    
    # Sort by release date (newest first)
    movies = movies.order_by('-release_date')
    
    context = {
        'movies': movies,
        'form': form,
        'page_title': 'Now Showing',
        'total_movies': movies.count(),
    }
    return render(request, 'movies/movie_list.html', context)


def coming_soon_movies(request):
    """
    Display list of coming soon movies with filtering
    """
    movies = Movie.objects.filter(status='coming_soon').prefetch_related('genres')
    
    # Filter by language
    if request.GET.get('language'):
        movies = movies.filter(language=request.GET.get('language'))
    
    # Search by title or director
    if request.GET.get('query'):
        query = request.GET.get('query')
        movies = movies.filter(
            Q(title__icontains=query) | 
            Q(director__icontains=query) |
            Q(description__icontains=query)
        )
    
    movies = movies.order_by('release_date')
    
    context = {
        'movies': movies,
        'page_title': 'Coming Soon',
        'total_movies': movies.count(),
    }
    return render(request, 'movies/coming_soon.html', context)


def movie_detail(request, pk):
    """
    Display detailed information about a movie including reviews and ratings
    """
    movie = get_object_or_404(Movie, pk=pk)
    reviews = movie.reviews.select_related('user').order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check if user has already reviewed this movie
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    context = {
        'movie': movie,
        'reviews': reviews,
        'average_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
        'user_review': user_review,
        'page_title': movie.title,
    }
    return render(request, 'movies/movie_detail.html', context)


@login_required(login_url='users:login')
@require_http_methods(["GET", "POST"])
def submit_review(request, pk):
    """
    Submit or update a review for a movie
    Only for authenticated users
    """
    movie = get_object_or_404(Movie, pk=pk)
    
    try:
        existing_review = MovieReview.objects.get(movie=movie, user=request.user)
        is_update = True
    except MovieReview.DoesNotExist:
        existing_review = None
        is_update = False
    
    if request.method == 'POST':
        form = MovieReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.rating = int(form.cleaned_data['rating'])  # Convert rating to integer
            
            # Check if user has booked tickets for this movie
            from bookings.models import Booking
            booking = Booking.objects.filter(
                user=request.user,
                show__movie=movie
            ).exists()
            review.is_verified_purchase = booking
            
            review.save()
            
            action = 'Updated' if is_update else 'Added'
            messages.success(request, f'{action} your review successfully!')
            return redirect('movies:movie_detail', pk=pk)
        else:
            messages.error(request, 'Error submitting review. Please check the form.')
    else:
        form = MovieReviewForm(instance=existing_review)
    
    context = {
        'form': form,
        'movie': movie,
        'is_update': is_update,
        'page_title': f'Review - {movie.title}',
    }
    return render(request, 'movies/submit_review.html', context)


def genre_list(request):
    """
    Display all available genres
    """
    genres = Genre.objects.annotate(movie_count=Count('movies')).filter(movie_count__gt=0)
    
    context = {
        'genres': genres,
        'page_title': 'Genres',
    }
    return render(request, 'movies/genre_list.html', context)


def movies_by_genre(request, genre_id):
    """
    Display all movies for a specific genre
    """
    genre = get_object_or_404(Genre, id=genre_id)
    movies = genre.movies.filter(status='running').annotate(
        review_count=Count('reviews'),
        average_rating=Avg('reviews__rating')
    ).order_by('-release_date')
    
    context = {
        'genre': genre,
        'movies': movies,
        'page_title': f'Movies - {genre.name}',
    }
    return render(request, 'movies/movies_by_genre.html', context)



@login_required(login_url='users:login')
@require_http_methods(["GET", "POST"])
def add_movie(request):
    """
    Add a new movie to the database. Only accessible to Admin and Theatre Manager roles.
    """
    # Role based access: allow superusers, users with UserRole 'admin' or 'theatre_manager'
    user = request.user
    user_role = None
    try:
        user_role = getattr(user, 'role').role
    except Exception:
        user_role = None

    if not (user.is_superuser or user_role in ['admin', 'theatre_manager']):
        return HttpResponseForbidden("You do not have permission to add movies.")

    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            messages.success(request, 'Movie added successfully.')
            return redirect('movies:movie_detail', pk=movie.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MovieForm()

    context = {
        'form': form,
        'page_title': 'Add Movie',
    }
    return render(request, 'movies/add_movie.html', context)
