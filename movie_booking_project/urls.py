"""
URL configuration for movie_booking_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from utils import views as utils_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # App URLs
    path('users/', include('users.urls', namespace='users')),
    path('movies/', include('movies.urls', namespace='movies')),
    path('theatres/', include('theatres.urls', namespace='theatres')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('food/', include('food.urls', namespace='food')),
    path('payments/', include('payments.urls', namespace='payments')),
    
    # Home
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', utils_views.contact, name='contact'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
