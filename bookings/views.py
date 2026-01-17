"""
Views for Bookings app
- Create bookings
- View booking history
- Download tickets
- Cancel bookings
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import FileResponse, JsonResponse, Http404
from django.db import transaction, IntegrityError
from .models import Booking, Ticket, BookingCancellation
from .forms import BookingForm, BookingCancellationForm
from theatres.models import Show, Seat
from payments.models import Payment
from decimal import Decimal
import os
from django.http import FileResponse
from io import BytesIO
from PIL import Image as PilImage, ImageDraw, ImageFont


@login_required(login_url='users:login')
@require_http_methods(["POST"])
def create_booking(request):
    """
    Create a new booking with selected seats
    """
    show_id = request.POST.get('show_id')
    seat_ids = request.POST.getlist('seats')
    discount = Decimal(request.POST.get('discount', 0))
    
    if not show_id or not seat_ids:
        messages.error(request, 'Please select a show and at least one seat.')
        return redirect('movies:movie_list')
    
    show = get_object_or_404(Show, id=show_id)
    seats = Seat.objects.filter(id__in=seat_ids)
    
    # Calculate total amount using Decimal for all calculations
    total_amount = sum((seat.base_price for seat in seats), Decimal('0'))
    tax = total_amount * Decimal('0.05')  # 5% tax
    final_amount = total_amount + tax - discount
    
    # Check seat availability first to avoid UNIQUE constraint violations
    already_booked = []
    for seat in seats:
        if Ticket.objects.filter(show=show, seat=seat).exists():
            try:
                label = f"{seat.row}{seat.seat_number}"
            except Exception:
                label = str(seat)
            already_booked.append(label)

    if already_booked:
        messages.error(request, 'Some selected seats are already booked: ' + ', '.join(already_booked))
        # Redirect back to the seat layout for this show
        return redirect('theatres:seat_layout', show_id=show.id)

    # Create booking and tickets inside a transaction so partial work is rolled back
    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                user=request.user,
                show=show,
                total_amount=total_amount,
                discount_amount=discount,
                final_amount=final_amount,
                status='pending'
            )

            # Create tickets for each seat
            seat_count = len(seats)
            for seat in seats:
                # If this show belongs to "Screen 2", override seat price to 300
                # Robustly detect Screen 2 by id or name variations
                screen = getattr(show, 'screen', None)
                screen_matches = False
                try:
                    if screen and getattr(screen, 'pk', None) == 2:
                        screen_matches = True
                except Exception:
                    pass

                try:
                    name = (getattr(screen, 'name', '') or '').strip().lower()
                except Exception:
                    name = ''

                if name in ('screen2', 'screen 2', '2') or name.endswith(' 2') or 'screen 2' in name:
                    screen_matches = True

                if screen_matches:
                    seat_price = Decimal('300.00')
                else:
                    seat_price = seat.base_price

                Ticket.objects.create(
                    booking=booking,
                    show=show,
                    seat=seat,
                    base_price=seat_price,
                    tax=(tax / Decimal(seat_count)),
                    final_price=(seat_price + (tax / Decimal(seat_count))) - (discount / Decimal(seat_count))
                )
    except IntegrityError:
        # This should be rare because we check availability above, but handle gracefully
        messages.error(request, 'A seat was just booked by someone else. Please try selecting seats again.')
        return redirect('theatres:seat_layout', show_id=show.id)
    
    messages.success(request, f'Booking created successfully! Booking ID: {booking.booking_id}')
    # Redirect to the payments app's payment gateway for this booking
    return redirect('payments:payment_gateway', booking_id=booking.pk)


@login_required(login_url='users:login')
def booking_detail(request, pk):
    """
    Display detailed information about a booking
    """
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    tickets = booking.tickets.all()
    payment = Payment.objects.filter(booking=booking).first()
    
    context = {
        'booking': booking,
        'tickets': tickets,
        'payment': payment,
        'page_title': f'Booking Details - {booking.booking_id}',
    }
    return render(request, 'bookings/booking_detail.html', context)


@login_required(login_url='users:login')
def booking_list(request):
    """
    Display all bookings for the logged-in user
    """
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'bookings': bookings,
        'page_title': 'My Bookings',
    }
    return render(request, 'bookings/booking_list.html', context)


@require_http_methods(["GET"])
def ticket_preview(request, ticket_id):
    """
    Display ticket details (preview page) when QR is scanned.
    Shows: Ticket ID, Movie, Show, Seat, Price, Booking ID with download button.
    """
    # Try lookup by ticket_id field. If that fails and numeric, try PK fallback.
    ticket = Ticket.objects.filter(ticket_id=ticket_id).first()

    if not ticket and str(ticket_id).isdigit():
        ticket = Ticket.objects.filter(pk=int(ticket_id)).first()

    if not ticket:
        raise Http404('Ticket not found.')

    # Build display data
    try:
        seat_label = f"{ticket.seat.row}{ticket.seat.seat_number}"
    except Exception:
        seat_label = str(ticket.seat)

    try:
        show_dt = f"{ticket.show.show_date} {ticket.show.show_time}"
    except Exception:
        show_dt = str(ticket.show)
    # Determine whether the ticket can be downloaded: not cancelled and payment completed
    can_download = False
    try:
        booking_status = ticket.booking.status
    except Exception:
        booking_status = None

    if booking_status != 'cancelled':
        try:
            from payments.models import Payment
            completed_payment = Payment.objects.filter(booking=ticket.booking, status='completed').first()
        except Exception:
            completed_payment = None

        if completed_payment:
            can_download = True

    context = {
        'ticket': ticket,
        'seat_label': seat_label,
        'show_dt': show_dt,
        'page_title': 'Ticket Details',
        'can_download': can_download,
    }
    return render(request, 'bookings/ticket_preview.html', context)


@require_http_methods(["GET"])
def download_ticket(request, ticket_id):
    """
    Download ticket as professional PDF. Public access: anyone with a valid ticket identifier
    can download the PDF (use with care — numeric PKs are less secure).
    """
    # Try lookup by ticket_id field (unique ticket identifier). If that fails
    # and the provided identifier is numeric, fall back to primary key lookup so
    # legacy numeric links (e.g. /ticket/14/download/) keep working.
    ticket = Ticket.objects.filter(ticket_id=ticket_id).first()

    if not ticket and str(ticket_id).isdigit():
        ticket = Ticket.objects.filter(pk=int(ticket_id)).first()

    if not ticket:
        # Not found — raise 404 so it's clear to callers
        raise Http404('Ticket not found.')

    # Prevent downloads for cancelled bookings
    try:
        booking_status = ticket.booking.status
    except Exception:
        booking_status = None

    if booking_status == 'cancelled':
        # If the requester is the booking owner, show a friendly message and redirect
        if request.user.is_authenticated and ticket.booking.user == request.user:
            messages.error(request, 'Cannot download ticket for a cancelled booking.')
            return redirect('bookings:booking_detail', pk=ticket.booking.pk)
        # For others, return 404 to avoid leaking existence
        raise Http404('Ticket not available.')

    # Require completed payment before allowing download
    try:
        from payments.models import Payment
        completed_payment = Payment.objects.filter(booking=ticket.booking, status='completed').first()
    except Exception:
        completed_payment = None

    if not completed_payment:
        # If the requester is the booking owner, redirect them with a message
        if request.user.is_authenticated and ticket.booking.user == request.user:
            messages.error(request, 'Payment is required to download this ticket.')
            return redirect('bookings:booking_detail', pk=ticket.booking.pk)
        # For others, do not reveal existence
        raise Http404('Ticket not available.')

    # Serve a professional PDF ticket with details and embedded QR code
    if ticket.qr_code and ticket.qr_code.name:
        try:
            # Build a ticket image using Pillow and save as PDF in-memory
            from PIL import Image as PilImage, ImageDraw, ImageFont
            
            # Create canvas (A4 page)
            width, height = (595, 842)
            canvas = PilImage.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(canvas)

            # Load fonts
            try:
                font_title = ImageFont.truetype('arial.ttf', 32)
                font_subtitle = ImageFont.truetype('arial.ttf', 18)
                font_normal = ImageFont.truetype('arial.ttf', 13)
                font_label = ImageFont.truetype('arial.ttf', 11)
                font_small = ImageFont.truetype('arial.ttf', 10)
            except Exception:
                font_title = ImageFont.load_default()
                font_subtitle = ImageFont.load_default()
                font_normal = ImageFont.load_default()
                font_label = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Color scheme
            primary_color = (102, 126, 234)  # #667eea
            secondary_color = (118, 75, 162)  # #764ba2
            accent_color = (16, 185, 129)  # #10b981
            text_dark = (45, 45, 45)  # #2d2d2d
            border_color = (220, 220, 220)  # #dcdcdc

            # ===== HEADER SECTION =====
            header_height = 100
            draw.rectangle([(0, 0), (width, header_height)], fill=primary_color)
            
            # Cinema logo/branding
            draw.text((30, 20), '🎬 CineBook', font=font_title, fill='white')
            draw.text((30, 60), 'Premium Cinema Tickets', font=font_label, fill='white')

            # ===== MAIN TICKET SECTION =====
            ticket_x_start = 30
            ticket_y_start = 120
            ticket_width = width - 60
            ticket_height = 420
            ticket_x_end = ticket_x_start + ticket_width
            ticket_y_end = ticket_y_start + ticket_height

            # Main ticket border (thick outer border)
            draw.rectangle(
                [(ticket_x_start, ticket_y_start), (ticket_x_end, ticket_y_end)],
                outline=primary_color,
                width=3
            )

            # Decorative corner elements
            corner_size = 15
            corners = [
                (ticket_x_start, ticket_y_start),
                (ticket_x_end - corner_size, ticket_y_start),
                (ticket_x_start, ticket_y_end - corner_size),
                (ticket_x_end - corner_size, ticket_y_end - corner_size)
            ]
            for corner in corners:
                draw.rectangle([corner, (corner[0] + corner_size, corner[1] + corner_size)], fill=secondary_color)

            # ===== LEFT SECTION (Ticket Details) =====
            left_x = ticket_x_start + 20
            left_y = ticket_y_start + 20
            divider_x = ticket_x_start + 340

            # Movie title (large)
            movie_title = ticket.show.movie.title[:40]  # Truncate if too long
            draw.text((left_x, left_y), movie_title, font=font_subtitle, fill=text_dark)
            left_y += 35

            # Decorative line
            draw.line([(left_x, left_y), (divider_x - 20, left_y)], fill=border_color, width=2)
            left_y += 15

            # Ticket number with barcode style
            ticket_id_text = f'#{ticket.ticket_id}'
            draw.text((left_x, left_y), 'TICKET ID', font=font_label, fill=secondary_color)
            draw.text((left_x, left_y + 14), ticket_id_text, font=ImageFont.truetype('arial.ttf', 16) if font_normal else font_normal, fill=primary_color)
            left_y += 50

            # Show details
            draw.text((left_x, left_y), 'SHOW DETAILS', font=font_label, fill=secondary_color)
            left_y += 15
            
            try:
                show_date = str(ticket.show.show_date)
                show_time = str(ticket.show.show_time)
            except Exception:
                show_date = 'N/A'
                show_time = 'N/A'
            
            draw.text((left_x, left_y), f'Date: {show_date}', font=font_normal, fill=text_dark)
            left_y += 20
            draw.text((left_x, left_y), f'Time: {show_time}', font=font_normal, fill=text_dark)
            left_y += 25

            # Seat information (highlighted)
            try:
                seat_label = f'{ticket.seat.row}{ticket.seat.seat_number}'
            except Exception:
                seat_label = 'N/A'

            seat_box_y = left_y
            draw.rectangle([(left_x - 5, seat_box_y - 5), (divider_x - 25, seat_box_y + 45)], fill=accent_color, outline=accent_color)
            draw.text((left_x, seat_box_y), 'SEAT', font=font_label, fill='white')
            draw.text((left_x, seat_box_y + 18), seat_label, font=ImageFont.truetype('arial.ttf', 24) if font_normal else font_normal, fill='white')

            # ===== RIGHT SECTION (QR Code) =====
            qr_size = 200
            qr_x = divider_x + 20
            qr_y = ticket_y_start + 60

            try:
                qr_img = PilImage.open(ticket.qr_code.path).convert('RGB')
                qr_img = qr_img.resize((qr_size, qr_size))
                # Add white border around QR code
                qr_with_border = PilImage.new('RGB', (qr_size + 8, qr_size + 8), 'white')
                qr_with_border.paste(qr_img, (4, 4))
                canvas.paste(qr_with_border, (qr_x, qr_y))
            except Exception:
                # Placeholder for QR code
                draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], outline=border_color, width=2)
                draw.text((qr_x + 30, qr_y + 90), 'QR Code', font=font_label, fill=text_dark)

            draw.text((qr_x, qr_y + qr_size + 15), 'Scan for entry', font=font_small, fill=text_dark)

            # Booking reference and price
            left_y += 70
            draw.line([(left_x, left_y), (divider_x - 20, left_y)], fill=border_color, width=1)
            left_y += 15

            draw.text((left_x, left_y), f'Booking Ref: {ticket.booking.booking_id}', font=font_label, fill=secondary_color)
            left_y += 18

            try:
                price_str = f'₹ {ticket.final_price}'
            except Exception:
                price_str = '₹ 0'

            draw.text((left_x, left_y), f'Price: {price_str}', font=font_normal, fill=text_dark)

            # ===== FOOTER SECTION =====
            footer_y = ticket_y_end + 20
            
            # Important information box
            draw.rectangle(
                [(ticket_x_start, footer_y), (ticket_x_end, footer_y + 100)],
                outline=border_color,
                width=1
            )
            
            info_y = footer_y + 10
            draw.text((ticket_x_start + 15, info_y), '✓ IMPORTANT INFORMATION', font=font_label, fill=primary_color)
            info_y += 18
            
            info_lines = [
                '• Present this ticket (printed or digital) at theatre entrance',
                '• Arrive 15 minutes before show time',
                '• Valid only for the specified show, date, and seat',
                '• Non-transferable and non-refundable after show starts'
            ]
            
            for line in info_lines:
                draw.text((ticket_x_start + 15, info_y), line, font=font_small, fill=text_dark)
                info_y += 15

            # Bottom policy text
            policy_y = height - 40
            draw.text((ticket_x_start, policy_y), 'www.cinebook.in | support@cinebook.in | Call: 1800-CINEBOOK', 
                     font=font_small, fill=secondary_color)
            policy_y += 15
            draw.text((ticket_x_start, policy_y), f'Generated on {ticket.booking.created_at.strftime("%d %b %Y")}', 
                     font=font_small, fill='gray')

            # Save to BytesIO as PDF
            from io import BytesIO
            buf = BytesIO()
            canvas.save(buf, format='PDF')
            buf.seek(0)

            response = FileResponse(buf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="CineBook_Ticket_{ticket.ticket_id}.pdf"'
            return response
            
        except FileNotFoundError:
            # If the file is missing on disk, show an informative page for owners if possible
            if request.user.is_authenticated and ticket.booking.user == request.user:
                messages.error(request, 'Ticket file is missing on server.')
                return redirect('bookings:booking_detail', pk=ticket.booking.pk)
            raise Http404('Ticket file is missing on server.')

    # No QR code stored
    if request.user.is_authenticated and ticket.booking.user == request.user:
        messages.error(request, 'Ticket QR code not available.')
        return redirect('bookings:booking_detail', pk=ticket.booking.pk)
    raise Http404('Ticket QR code not available.')


@login_required(login_url='users:login')
@require_http_methods(["GET", "POST"])
def cancel_booking(request, pk):
    """
    Cancel a booking and process refund
    """
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    
    # Check if booking can be cancelled
    if booking.status != 'confirmed':
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:booking_detail', pk=booking.pk)
    
    if request.method == 'POST':
        form = BookingCancellationForm(request.POST)
        if form.is_valid():
            cancellation = form.save(commit=False)
            cancellation.booking = booking
            cancellation.cancelled_by = request.user
            
            # Calculate refund
            cancellation.refund_amount = booking.final_amount - cancellation.cancellation_charges
            cancellation.save()
            
            # Update booking status
            booking.status = 'cancelled'
            booking.save()
            
            messages.success(request, f'Booking cancelled. Refund: {cancellation.refund_amount}')
            return redirect('bookings:booking_list')
        else:
            messages.error(request, 'Error processing cancellation.')
    else:
        form = BookingCancellationForm()
    
    context = {
        'form': form,
        'booking': booking,
        'page_title': 'Cancel Booking',
    }
    return render(request, 'bookings/cancel_booking.html', context)


@login_required(login_url='users:login')
@require_http_methods(["GET"])
def booking_confirmation(request, pk):
    """
    Display booking confirmation after successful payment
    """
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    payment = Payment.objects.filter(booking=booking, status='completed').first()
    
    if not payment:
        messages.warning(request, 'Payment not confirmed yet.')
        return redirect('bookings:booking_detail', pk=booking.pk)
    
    context = {
        'booking': booking,
        'payment': payment,
        'page_title': 'Booking Confirmed',
    }
    return render(request, 'bookings/booking_confirmation.html', context)


@login_required(login_url='users:login')
@require_http_methods(["GET"])
def booking_download(request, pk):
    """
    Generate a multi-page PDF containing all tickets for a booking, each page
    contains ticket details and embedded QR code image with professional design.
    """
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    # Ensure payment completed
    try:
        completed_payment = Payment.objects.filter(booking=booking, status='completed').first()
    except Exception:
        completed_payment = None

    if not completed_payment:
        messages.error(request, 'Payment required to download tickets.')
        return redirect('bookings:booking_detail', pk=booking.pk)

    tickets = booking.tickets.all()
    if not tickets:
        messages.error(request, 'No tickets available for this booking.')
        return redirect('bookings:booking_detail', pk=booking.pk)

    pages = []
    # PDF page size (A4-like) in pixels for Pillow at 72 DPI
    width, height = (595, 842)

    # Try to load a TTF font, fall back to default
    try:
        font_title = ImageFont.truetype('arial.ttf', 32)
        font_subtitle = ImageFont.truetype('arial.ttf', 18)
        font_normal = ImageFont.truetype('arial.ttf', 13)
        font_label = ImageFont.truetype('arial.ttf', 11)
        font_small = ImageFont.truetype('arial.ttf', 10)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Color scheme (matching CineBook theme)
    primary_color = (102, 126, 234)  # #667eea
    secondary_color = (118, 75, 162)  # #764ba2
    accent_color = (16, 185, 129)  # #10b981
    text_dark = (45, 45, 45)  # #2d2d2d
    border_color = (220, 220, 220)  # #dcdcdc
    gold_color = (212, 175, 55)  # #d4af37 - premium gold

    for idx, ticket in enumerate(tickets):
        canvas = PilImage.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(canvas)

        # ===== HEADER SECTION =====
        header_height = 100
        draw.rectangle([(0, 0), (width, header_height)], fill=primary_color)
        
        # Cinema logo/branding
        draw.text((30, 20), '🎬 CineBook', font=font_title, fill='white')
        draw.text((30, 60), 'Premium Cinema Tickets', font=font_label, fill='white')

        # ===== MAIN TICKET SECTION =====
        ticket_x_start = 30
        ticket_y_start = 120
        ticket_width = width - 60
        ticket_height = 420
        ticket_x_end = ticket_x_start + ticket_width
        ticket_y_end = ticket_y_start + ticket_height

        # Main ticket border (thick outer border)
        draw.rectangle(
            [(ticket_x_start, ticket_y_start), (ticket_x_end, ticket_y_end)],
            outline=primary_color,
            width=3
        )

        # Decorative corner elements
        corner_size = 15
        corners = [
            (ticket_x_start, ticket_y_start),
            (ticket_x_end - corner_size, ticket_y_start),
            (ticket_x_start, ticket_y_end - corner_size),
            (ticket_x_end - corner_size, ticket_y_end - corner_size)
        ]
        for corner in corners:
            draw.rectangle([corner, (corner[0] + corner_size, corner[1] + corner_size)], fill=secondary_color)

        # ===== LEFT SECTION (Ticket Details) =====
        left_x = ticket_x_start + 20
        left_y = ticket_y_start + 20
        divider_x = ticket_x_start + 340

        # Movie title (large)
        movie_title = ticket.show.movie.title[:40]  # Truncate if too long
        draw.text((left_x, left_y), movie_title, font=font_subtitle, fill=text_dark)
        left_y += 35

        # Decorative line
        draw.line([(left_x, left_y), (divider_x - 20, left_y)], fill=border_color, width=2)
        left_y += 15

        # Ticket number with barcode style
        ticket_id_text = f'#{ticket.ticket_id}'
        draw.text((left_x, left_y), 'TICKET ID', font=font_label, fill=secondary_color)
        draw.text((left_x, left_y + 14), ticket_id_text, font=ImageFont.truetype('arial.ttf', 16) if font_normal else font_normal, fill=primary_color)
        left_y += 50

        # Show details
        draw.text((left_x, left_y), 'SHOW DETAILS', font=font_label, fill=secondary_color)
        left_y += 15
        
        try:
            show_date = str(ticket.show.show_date)
            show_time = str(ticket.show.show_time)
        except Exception:
            show_date = 'N/A'
            show_time = 'N/A'
        
        draw.text((left_x, left_y), f'Date: {show_date}', font=font_normal, fill=text_dark)
        left_y += 20
        draw.text((left_x, left_y), f'Time: {show_time}', font=font_normal, fill=text_dark)
        left_y += 25

        # Seat information (highlighted)
        try:
            seat_label = f'{ticket.seat.row}{ticket.seat.seat_number}'
        except Exception:
            seat_label = 'N/A'

        seat_box_y = left_y
        draw.rectangle([(left_x - 5, seat_box_y - 5), (divider_x - 25, seat_box_y + 45)], fill=accent_color, outline=accent_color)
        draw.text((left_x, seat_box_y), 'SEAT', font=font_label, fill='white')
        draw.text((left_x, seat_box_y + 18), seat_label, font=ImageFont.truetype('arial.ttf', 24) if font_normal else font_normal, fill='white')

        # ===== RIGHT SECTION (QR Code) =====
        qr_size = 200
        qr_x = divider_x + 20
        qr_y = ticket_y_start + 60

        if ticket.qr_code and ticket.qr_code.path:
            try:
                qr_img = PilImage.open(ticket.qr_code.path).convert('RGB')
                qr_img = qr_img.resize((qr_size, qr_size))
                # Add white border around QR code
                qr_with_border = PilImage.new('RGB', (qr_size + 8, qr_size + 8), 'white')
                qr_with_border.paste(qr_img, (4, 4))
                canvas.paste(qr_with_border, (qr_x, qr_y))
            except Exception:
                # Placeholder for QR code
                draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], outline=border_color, width=2)
                draw.text((qr_x + 30, qr_y + 90), 'QR Code', font=font_label, fill=text_dark)

        draw.text((qr_x, qr_y + qr_size + 15), 'Scan for entry', font=font_small, fill=text_dark)

        # Booking reference and price
        left_y += 70
        draw.line([(left_x, left_y), (divider_x - 20, left_y)], fill=border_color, width=1)
        left_y += 15

        draw.text((left_x, left_y), f'Booking Ref: {booking.booking_id}', font=font_label, fill=secondary_color)
        left_y += 18

        try:
            price_str = f'₹ {ticket.final_price}'
        except Exception:
            price_str = '₹ 0'

        draw.text((left_x, left_y), f'Price: {price_str}', font=font_normal, fill=text_dark)
        left_y += 20

        # ===== FOOTER SECTION =====
        footer_y = ticket_y_end + 20
        
        # Important information box
        draw.rectangle(
            [(ticket_x_start, footer_y), (ticket_x_end, footer_y + 100)],
            outline=border_color,
            width=1
        )
        
        info_y = footer_y + 10
        draw.text((ticket_x_start + 15, info_y), '✓ IMPORTANT INFORMATION', font=font_label, fill=primary_color)
        info_y += 18
        
        info_lines = [
            '• Present this ticket (printed or digital) at theatre entrance',
            '• Arrive 15 minutes before show time',
            '• Valid only for the specified show, date, and seat',
            '• Non-transferable and non-refundable after show starts'
        ]
        
        for line in info_lines:
            draw.text((ticket_x_start + 15, info_y), line, font=font_small, fill=text_dark)
            info_y += 15

        # Bottom policy text
        policy_y = height - 40
        draw.text((ticket_x_start, policy_y), 'www.cinebook.in | support@cinebook.in | Call: 1800-CINEBOOK', 
                 font=font_small, fill=secondary_color)
        policy_y += 15
        draw.text((ticket_x_start, policy_y), f'Page {idx + 1} of {len(tickets)} | Generated on {booking.created_at.strftime("%d %b %Y")}', 
                 font=font_small, fill='gray')

        pages.append(canvas)

    # Save pages to a single PDF in-memory
    buf = BytesIO()
    try:
        if len(pages) == 1:
            pages[0].save(buf, format='PDF')
        else:
            pages[0].save(buf, format='PDF', save_all=True, append_images=pages[1:])
        buf.seek(0)
        response = FileResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="CineBook_Tickets_{booking.booking_id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Could not generate PDF: {e}')
        return redirect('bookings:booking_detail', pk=booking.pk)
