from django.core.management.base import BaseCommand
from django.db import transaction
from movies.models import Movie, Genre
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Seed movies: 10 Now Showing and 10 Coming Soon'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Get or create genres
            action = Genre.objects.get_or_create(name='Action')[0]
            drama = Genre.objects.get_or_create(name='Drama')[0]
            comedy = Genre.objects.get_or_create(name='Comedy')[0]
            thriller = Genre.objects.get_or_create(name='Thriller')[0]
            romance = Genre.objects.get_or_create(name='Romance')[0]
            
            # 10 Now Showing movies
            now_showing_movies = [
                {
                    'title': 'The Great Adventure',
                    'description': 'An epic adventure film filled with action and thrills.',
                    'release_date': (datetime.now() - timedelta(days=30)).date(),
                    'duration_minutes': 145,
                    'language': 'english',
                    'rating': 8.5,
                    'director': 'Christopher Nolan',
                    'cast': 'Leonardo DiCaprio, Scarlett Johansson',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [action, drama],
                },
                {
                    'title': 'Love in Paris',
                    'description': 'A romantic drama set in the City of Light.',
                    'release_date': (datetime.now() - timedelta(days=20)).date(),
                    'duration_minutes': 128,
                    'language': 'english',
                    'rating': 7.8,
                    'director': 'Greta Gerwig',
                    'cast': 'Timothée Chalamet, Florence Pugh',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [romance, drama],
                },
                {
                    'title': 'Laugh Out Loud',
                    'description': 'A hilarious comedy that will keep you laughing.',
                    'release_date': (datetime.now() - timedelta(days=15)).date(),
                    'duration_minutes': 105,
                    'language': 'hindi',
                    'rating': 7.2,
                    'director': 'Rajkumar Hirani',
                    'cast': 'Shah Rukh Khan, Anushka Sharma',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [comedy],
                },
                {
                    'title': 'Dark Secrets',
                    'description': 'A thrilling mystery with unexpected twists.',
                    'release_date': (datetime.now() - timedelta(days=10)).date(),
                    'duration_minutes': 135,
                    'language': 'english',
                    'rating': 8.1,
                    'director': 'Denis Villeneuve',
                    'cast': 'Tom Hardy, Charlize Theron',
                    'certification': 'A',
                    'status': 'running',
                    'genres': [thriller, drama],
                },
                {
                    'title': 'Warriors: Rise of Heroes',
                    'description': 'An action-packed superhero film with stunning visuals.',
                    'release_date': (datetime.now() - timedelta(days=5)).date(),
                    'duration_minutes': 152,
                    'language': 'english',
                    'rating': 8.3,
                    'director': 'The Russo Brothers',
                    'cast': 'Tom Cruise, Zendaya',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [action],
                },
                {
                    'title': 'The Last Dance',
                    'description': 'A romantic drama about second chances and new beginnings.',
                    'release_date': (datetime.now() - timedelta(days=8)).date(),
                    'duration_minutes': 118,
                    'language': 'english',
                    'rating': 7.5,
                    'director': 'Damien Chazelle',
                    'cast': 'Ryan Gosling, Emma Stone',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [romance, drama],
                },
                {
                    'title': 'Comedy Gold',
                    'description': 'A side-splitting comedy with unforgettable characters.',
                    'release_date': (datetime.now() - timedelta(days=3)).date(),
                    'duration_minutes': 112,
                    'language': 'hindi',
                    'rating': 7.9,
                    'director': 'Raj Mehta',
                    'cast': 'Akshay Kumar, Kriti Sanon',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [comedy],
                },
                {
                    'title': 'Silent Thunder',
                    'description': 'A gripping thriller about espionage and betrayal.',
                    'release_date': (datetime.now() - timedelta(days=2)).date(),
                    'duration_minutes': 142,
                    'language': 'english',
                    'rating': 8.0,
                    'director': 'Kathryn Bigelow',
                    'cast': 'Jessica Chastain, Michael B. Jordan',
                    'certification': 'A',
                    'status': 'running',
                    'genres': [thriller, action],
                },
                {
                    'title': 'Eternal Hope',
                    'description': 'An inspiring drama about overcoming adversity.',
                    'release_date': (datetime.now() - timedelta(days=1)).date(),
                    'duration_minutes': 138,
                    'language': 'english',
                    'rating': 7.6,
                    'director': 'Barry Jenkins',
                    'cast': 'Mahershala Ali, Naomie Harris',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [drama],
                },
                {
                    'title': 'Game Masters',
                    'description': 'An action adventure about gamers saving the real world.',
                    'release_date': datetime.now().date(),
                    'duration_minutes': 125,
                    'language': 'english',
                    'rating': 7.7,
                    'director': 'Shawn Levy',
                    'cast': 'Tom Holland, Zoe Saldana',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [action, comedy],
                },
                {
                    'title': 'Aai',
                    'description': 'A touching story about the bond between mother and son.',
                    'release_date': (datetime.now() - timedelta(days=25)).date(),
                    'duration_minutes': 135,
                    'language': 'marathi',
                    'rating': 8.2,
                    'director': 'Mahesh Manjrekar',
                    'cast': 'Supriya Pathare, Sachin Khedekar',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [drama],
                },
                {
                    'title': 'Natrang',
                    'description': 'A brilliant story of a man\'s passion for theatre.',
                    'release_date': (datetime.now() - timedelta(days=18)).date(),
                    'duration_minutes': 112,
                    'language': 'marathi',
                    'rating': 8.0,
                    'director': 'Ravi Jadhav',
                    'cast': 'Medha Manjrekar, Atul Kulkarni',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [drama, comedy],
                },
                {
                    'title': 'Sairat',
                    'description': 'A gripping tale of young love and family conflict.',
                    'release_date': (datetime.now() - timedelta(days=12)).date(),
                    'duration_minutes': 141,
                    'language': 'marathi',
                    'rating': 7.9,
                    'director': 'Nagraj Manjule',
                    'cast': 'Rinku Rajguru, Akash Thosar',
                    'certification': 'UA',
                    'status': 'running',
                    'genres': [romance, drama],
                },
            ]
            
            # 10 Coming Soon movies
            coming_soon_movies = [
                {
                    'title': 'Future Legends',
                    'description': 'An epic sci-fi saga about humanity\'s future.',
                    'release_date': (datetime.now() + timedelta(days=45)).date(),
                    'duration_minutes': 158,
                    'language': 'english',
                    'rating': 0.0,
                    'director': 'James Cameron',
                    'cast': 'Pedro Pascal, Anya Taylor-Joy',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [action, drama],
                },
                {
                    'title': 'Heartbeat Promise',
                    'description': 'A touching romance spanning decades.',
                    'release_date': (datetime.now() + timedelta(days=30)).date(),
                    'duration_minutes': 124,
                    'language': 'english',
                    'rating': 0.0,
                    'director': 'Luca Guadagnino',
                    'cast': 'Timothée Chalamet, Rebecca Ferguson',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [romance, drama],
                },
                {
                    'title': 'Jokes Unleashed',
                    'description': 'A comedy extravaganza with laugh-out-loud moments.',
                    'release_date': (datetime.now() + timedelta(days=20)).date(),
                    'duration_minutes': 110,
                    'language': 'hindi',
                    'rating': 0.0,
                    'director': 'Abhishek Dudhaiya',
                    'cast': 'Ranveer Singh, Deepika Padukone',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [comedy],
                },
                {
                    'title': 'Shadows of Deception',
                    'description': 'A mind-bending thriller with shocking revelations.',
                    'release_date': (datetime.now() + timedelta(days=50)).date(),
                    'duration_minutes': 148,
                    'language': 'english',
                    'rating': 0.0,
                    'director': 'Ari Aster',
                    'cast': 'Oscar Isaac, Tilda Swinton',
                    'certification': 'A',
                    'status': 'coming_soon',
                    'genres': [thriller, drama],
                },
                {
                    'title': 'Super Strikes Back',
                    'description': 'The superhero returns for an even bigger adventure.',
                    'release_date': (datetime.now() + timedelta(days=60)).date(),
                    'duration_minutes': 159,
                    'language': 'english',
                    'rating': 0.0,
                    'director': 'Sam Raimi',
                    'cast': 'Benedict Cumberbatch, Elizabeth Olsen',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [action, drama],
                },
                {
                    'title': 'Second Chances',
                    'description': 'A romantic tale of rekindling lost love.',
                    'release_date': (datetime.now() + timedelta(days=25)).date(),
                    'duration_minutes': 121,
                    'language': 'english',
                    'rating': 0.0,
                    'director': 'Richard Curtis',
                    'cast': 'Hugh Grant, Emma Watson',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [romance, comedy],
                },
                {
                    'title': 'Funny Business',
                    'description': 'Corporate comedy with quirky characters.',
                    'release_date': (datetime.now() + timedelta(days=35)).date(),
                    'duration_minutes': 115,
                    'language': 'hindi',
                    'rating': 0.0,
                    'director': 'Vikas Bahl',
                    'cast': 'Pankaj Tripathi, Kriti Kharbanda',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [comedy],
                },
                {
                    'title': 'Midnight Conspiracy',
                    'description': 'A political thriller with high stakes and danger.',
                    'release_date': (datetime.now() + timedelta(days=55)).date(),
                    'duration_minutes': 144,
                    'language': 'english',
                    'rating': 0.0,
                    'director': 'Jeff Nichols',
                    'cast': 'Cillian Murphy, Saoirse Ronan',
                    'certification': 'A',
                    'status': 'coming_soon',
                    'genres': [thriller, drama],
                },
                {
                    'title': 'Life\'s Colors',
                    'description': 'An uplifting drama about family and acceptance.',
                    'release_date': (datetime.now() + timedelta(days=28)).date(),
                    'duration_minutes': 134,
                    'language': 'english',
                    'rating': 0.0,
                    'director': 'Chloé Zhao',
                    'cast': 'Thomasin McKenzie, Paul Mescal',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [drama],
                },
                {
                    'title': 'Cyber Warriors',
                    'description': 'A sci-fi action adventure in a digital world.',
                    'release_date': (datetime.now() + timedelta(days=70)).date(),
                    'duration_minutes': 150,
                    'language': 'english',
                    'rating': 0.0,
                    'director': 'Taika Waititi',
                    'cast': 'Oscar Isaac, Dev Patel',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [action, drama],
                },
                {
                    'title': 'Natasamrat',
                    'description': 'A powerful drama about an aged actor\'s struggle.',
                    'release_date': (datetime.now() + timedelta(days=32)).date(),
                    'duration_minutes': 152,
                    'language': 'marathi',
                    'rating': 0.0,
                    'director': 'Mahesh Manjrekar',
                    'cast': 'Medha Manjrekar, Sachin Khedekar',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [drama],
                },
                {
                    'title': 'Fandry',
                    'description': 'A realistic portrayal of rural Marathi life and society.',
                    'release_date': (datetime.now() + timedelta(days=48)).date(),
                    'duration_minutes': 118,
                    'language': 'marathi',
                    'rating': 0.0,
                    'director': 'Nagraj Manjule',
                    'cast': 'Akash Thosar, Mrunal Thakur',
                    'certification': 'A',
                    'status': 'coming_soon',
                    'genres': [drama],
                },
                {
                    'title': 'Katyar Kaljat Ghusli',
                    'description': 'A beautiful tale of music and mentorship.',
                    'release_date': (datetime.now() + timedelta(days=42)).date(),
                    'duration_minutes': 146,
                    'language': 'marathi',
                    'rating': 0.0,
                    'director': 'Mahesh Manjrekar',
                    'cast': 'Sachin Khedekar, Atul Kulkarni',
                    'certification': 'UA',
                    'status': 'coming_soon',
                    'genres': [drama, romance],
                },
            ]
            
            # Create Now Showing movies in 3 languages: English, Hindi, Marathi
            languages = ['english', 'hindi', 'marathi']
            lang_labels = {'english': '(English)', 'hindi': '(Hindi)', 'marathi': '(Marathi)'}
            
            for movie_data in now_showing_movies:
                genres = movie_data.pop('genres')
                base_title = movie_data['title']
                
                for lang in languages:
                    # Modify title to include language
                    movie_data['title'] = f"{base_title} {lang_labels[lang]}"
                    movie_data['language'] = lang
                    
                    movie, created = Movie.objects.get_or_create(
                        title=movie_data['title'],
                        defaults=movie_data
                    )
                    movie.genres.set(genres)
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"✓ Created: {movie.title} (Running)"))
                    else:
                        self.stdout.write(self.style.NOTICE(f"~ Already exists: {movie.title}"))
            
            # Create Coming Soon movies in 3 languages: English, Hindi, Marathi
            languages = ['english', 'hindi', 'marathi']
            lang_labels = {'english': '(English)', 'hindi': '(Hindi)', 'marathi': '(Marathi)'}
            
            for movie_data in coming_soon_movies:
                genres = movie_data.pop('genres')
                base_title = movie_data['title']
                
                for lang in languages:
                    # Modify title to include language
                    movie_data['title'] = f"{base_title} {lang_labels[lang]}"
                    movie_data['language'] = lang
                    
                    movie, created = Movie.objects.get_or_create(
                        title=movie_data['title'],
                        defaults=movie_data
                    )
                    movie.genres.set(genres)
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"✓ Created: {movie.title} (Coming Soon)"))
                    else:
                        self.stdout.write(self.style.NOTICE(f"~ Already exists: {movie.title}"))
            
            self.stdout.write(self.style.SUCCESS('✓ Movie seeding complete: 10 Now Showing + 30 Coming Soon (10 movies × 3 languages)'))
