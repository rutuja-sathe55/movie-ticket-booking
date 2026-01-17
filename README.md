# CineBook - Django Movie Ticket Booking Website

A comprehensive Django-based movie ticket booking application with support for multiple theatres, shows, seat selection, food ordering, and online payments using Razorpay.

## Features

### 1. **User Management**
- User registration and authentication
- Role-based access (Admin, Theatre Manager, Customer, Staff, Guest)
- User profile management
- Email verification (ready for implementation)

### 2. **Movie Management**
- Browse movies with detailed information
- Filter by language, certification, genre
- Movie reviews and ratings
- Coming soon section
- Featured movies on homepage

### 3. **Theatre & Show Management**
- Multiple theatres with detailed information
- Multiple screens/halls per theatre
- Show management with date and time
- Screen amenities (4K, IMAX, Dolby)

### 4. **Seat Selection & Booking**
- Interactive seat layout
- Real-time seat availability
- Multiple seat types (Standard, Premium, VIP, Couple)
- QR code generation for tickets
- Booking confirmation and history

### 5. **Food Ordering**
- Menu with food categories
- Food item details and reviews
- Food order management
- Order status tracking (Pending, Preparing, Ready, Delivered)
- Staff assignment for food orders

### 6. **Payment Processing**
- Multiple payment methods
- Razorpay integration for online payments
- Payment status tracking
- Invoice generation
- Refund management

### 7. **Admin Panel**
- Comprehensive admin dashboard
- Manage movies, theatres, shows, seats
- User and role management
- Payment and refund tracking
- Order management

## Project Structure

```
movie_booking_project/
├── movie_booking_project/    # Main project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── users/                    # User authentication & profiles
├── movies/                   # Movie catalog & reviews
├── theatres/                 # Theatre & show management
├── bookings/                 # Ticket booking & management
├── food/                     # Food ordering system
├── payments/                 # Payment processing
├── utils/                    # Helper functions & utilities
├── templates/                # HTML templates
├── static/                   # CSS, JS, Images
├── manage.py
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites
- Python 3.8+
- Django 4.2+
- SQLite3 (or PostgreSQL for production)

### Setup Steps

1. **Clone the repository**
```bash
cd movie_booking_project
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create database**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Run development server**
```bash
python manage.py runserver
```

Access the application at `http://localhost:8000/`
Admin panel at `http://localhost:8000/admin/`

## Configuration

### Razorpay Integration
Update your Razorpay credentials in `settings.py`:
```python
RAZORPAY_KEY_ID = 'your_key_id'
RAZORPAY_KEY_SECRET = 'your_key_secret'
```

### Email Configuration
Configure email settings in `settings.py` for sending notifications:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your_email_host'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email'
EMAIL_HOST_PASSWORD = 'your_password'
```

## Database Schema

### Users App
- `User` (Django built-in)
- `UserProfile` - Extended user information
- `UserRole` - Role-based access
- `TheatreManager` - Theatre manager profile
- `Staff` - Staff profile for food operations

### Movies App
- `Movie` - Movie details
- `Genre` - Movie genres
- `MovieReview` - User reviews and ratings

### Theatres App
- `Theatre` - Cinema theatre information
- `Screen` - Individual screens/halls
- `Seat` - Individual seats
- `Show` - Movie screenings

### Bookings App
- `Booking` - Booking records
- `Ticket` - Individual tickets with QR codes
- `BookingCancellation` - Cancellation and refund tracking

### Food App
- `FoodCategory` - Food categories
- `FoodItem` - Menu items
- `FoodOrder` - Customer food orders
- `FoodOrderItem` - Line items in orders
- `FoodReview` - Food reviews

### Payments App
- `Payment` - Payment records
- `PaymentMethod` - Available payment methods
- `Refund` - Refund records
- `Invoice` - Invoice generation

## API Endpoints

### Utils API
- `GET /utils/api/seats/<show_id>/` - Get available seats for a show
- `GET /utils/api/seat-status/<show_id>/` - Get real-time seat status

## User Roles & Permissions

### Admin
- Full CRUD on all entities
- Manage users and roles
- View all bookings and payments
- Access to all reports

### Theatre Manager
- Manage shows and timings
- View theatre bookings and revenue
- Monitor seat availability
- Manage staff

### Customer
- Browse movies and theatres
- Book tickets
- Order food
- View booking history
- Submit reviews

### Staff
- Manage food orders
- Update order status
- Track deliveries

### Guest
- Browse movies and theatres
- View showtimes
- Cannot book or order

## Key Features Explained

### QR Code Generation
Automatic QR code generation for each ticket for easy entry verification at the cinema.

### Real-time Seat Availability
AJAX endpoints provide real-time seat status to prevent double bookings.

### Responsive Design
Mobile-friendly interface using Bootstrap 5.

### Role-based Access Control
Different user roles have different permissions and interfaces.

### Email Notifications
Automatic email notifications for bookings, payments, cancellations, and food order status.

## Testing the Application

### Sample Data Creation
1. Create superuser account via `createsuperuser`
2. Log in to admin panel (`/admin/`)
3. Add sample movies, theatres, screens, and shows
4. Create food categories and items
5. Test booking flow

### Test Credentials
- Username: admin
- Password: (set during superuser creation)

## Troubleshooting

### Common Issues

1. **Migration errors**
```bash
python manage.py makemigrations --empty <app_name>
python manage.py migrate --fake-initial
```

2. **Static files not loading**
```bash
python manage.py collectstatic --noinput
```

3. **Database locked**
Delete `db.sqlite3` and run migrations again

## Future Enhancements

- Mobile app development
- Advanced analytics and reporting
- Email/SMS notifications
- Loyalty points system
- Group booking discounts
- Dynamic pricing
- Payment gateway diversification
- Real-time notifications using WebSockets
- AI-powered recommendations

## Contributing

Contributions are welcome! Please follow Django best practices and maintain code quality.

## License

MIT License - See LICENSE file for details

## Support

For support and queries:
- Email: support@cinebook.com
- Phone: +91 9876543210

---

**Developed with ❤️ using Django**
