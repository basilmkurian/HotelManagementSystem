from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from django.contrib import messages
from .models import User, Room, Booking, HousekeepingTask, InventoryItem, Review, Notification, SupplyRequest, Payment, SupplyUsage, PayrollRecord
from .forms import (
                    UserRegistrationForm, 
                    BookingForm, 
                    HousekeepingTaskForm, 
                    UserProfileForm, 
                    RoomForm, 
                    RoomCategoryForm,
                    AssignDutiesForm,
                    CheckInForm,
                    StaffForm,
                    SupplyRequestForm,
                    InventoryForm,
                    EditUserForm,
                    ReceptionistBookingForm
                    )
import random
from django.views.decorators.csrf import ensure_csrf_cookie
from decimal import Decimal
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.db import transaction
from django.urls import reverse
from django.db.models import Sum, Avg, Count, F
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST
import razorpay
import json
from django.conf import settings
from datetime import datetime

#----------------------------------------user authentication----------------------------------------

def home(request):
    """Renders the landing page of the application."""
    return render(request, 'landing_page.html')

def generate_2fa_code():
    """Generates a random 6-digit code for two-factor authentication."""
    return str(random.randint(100000, 999999))

def send_2fa_code(user, code):
    """Sends the 2FA verification code to user's email."""
    send_mail(
        'Your 2FA Code',
        f'Your verification code is: {code}',
        'from@example.com',
        [user.email],
        fail_silently=False,
    )

def register(request):
    """Handles user registration with form validation."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful!')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def password_reset(request):
    return render(request, 'registration/password_reset.html')

@ensure_csrf_cookie
def login_view(request):
    """Handles user login with optional 2FA verification."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.two_factor_enabled:
                code = generate_2fa_code()
                user.two_factor_code = code  
                user.save()
                request.session['user_id'] = user.id
                send_2fa_code(user, code)
                return redirect('verify_2fa')
            else:
                login(request, user)
                messages.success(request, 'Successfully logged in!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

@login_required
def dashboard(request):
    """Routes users to their role-specific dashboard."""
    user = request.user
    
    if user.role == User.ADMIN:
        return admin_dashboard(request)
    elif user.role == User.MANAGER:
        return manager_dashboard(request)
    elif user.role == User.RECEPTIONIST:
        return receptionist_dashboard(request)
    elif user.role == User.HOUSEKEEPING:
        return housekeeping_dashboard(request)
    else:
        return guest_dashboard(request)

def admin_dashboard(request):
    """Displays admin-specific dashboard with system-wide statistics."""
    context = {
        'user': request.user,
        'total_rooms': Room.objects.count(),
        'available_rooms': Room.objects.filter(status='AVAILABLE').count(),
        'occupied_rooms': Room.objects.filter(status='OCCUPIED').count(),
        'reserved_rooms': Room.objects.filter(status='RESERVED').count(),
        'recent_reviews': Review.objects.order_by('-created_at')[:5],
        'total_bookings': Booking.objects.count(),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

def manager_dashboard(request):
    """Displays manager-specific dashboard."""
    context = {
        'user': request.user,
        'todays_checkins': Booking.objects.filter(status='CHECKED_IN').count(),
        'todays_checkouts': Booking.objects.filter(status='CHECKED_OUT').count(),
        'pending_reservations': Booking.objects.filter(status='PENDING').count(),
        'cancelled_bookings': Booking.objects.filter(status='CANCELLED').count(),
    }
    return render(request, 'dashboard/manager_dashboard.html', context)

@login_required
def receptionist_dashboard(request):
    """Displays receptionist-specific dashboard."""
    if request.user.role != 'receptionist':
        messages.error(request, 'Unauthorized access')
        return redirect('dashboard')

    available_rooms = Room.objects.filter(status='AVAILABLE').count()
    reserved_rooms = Room.objects.filter(status='RESERVED').count()
    occupied_rooms = Room.objects.filter(status='OCCUPIED').count()
    maintenance_rooms = Room.objects.filter(status='MAINTENANCE').count()

    recent_bookings = Booking.objects.select_related('guest', 'room').order_by('-created_at')[:5]

    for booking in recent_bookings:
        print(f"Booking ID: {booking.id}, Status: {booking.status}")

    context = {
        'available_rooms': available_rooms,
        'reserved_rooms': reserved_rooms,
        'occupied_rooms': occupied_rooms,
        'maintenance_rooms': maintenance_rooms,
        'recent_bookings': recent_bookings,
    }

    return render(request, 'dashboard/receptionist_dashboard.html', context)

def housekeeping_dashboard(request):
    """Displays housekeeping-specific dashboard."""
    context = {
        'tasks': HousekeepingTask.objects.filter(
            assigned_to=request.user,
            status__in=['pending', 'in_progress']
        ).order_by('-priority', '-created_at'),
        'supplies': InventoryItem.objects.all(),
        'pending_requests': SupplyRequest.objects.filter(
            requested_by=request.user,
            status='pending'
        )
    }
    return render(request, 'dashboard/housekeeping_dashboard.html', context)

@login_required
def guest_dashboard(request):
    """Displays guest-specific dashboard with booking details and bills."""
    bookings = Booking.objects.filter(
        guest=request.user,
        status__in=['CONFIRMED', 'CHECKED_IN']
    ).order_by('-check_in_date')
    
    current_booking = bookings.first()
    bills = None
    has_review = False
    review = None
    feedback = None
    
    if current_booking:
        total_nights = (current_booking.check_out_date - current_booking.check_in_date).days
        room_charges = current_booking.room.category.base_price * total_nights
        service_charges = current_booking.service_charges
        tax_amount = (room_charges + service_charges) * Decimal('0.18')
        total = round(room_charges + service_charges + tax_amount, 2)
        
        bills = {
            'room_charges': round(room_charges, 2),
            'service_charges': round(service_charges, 2),
            'tax_amount': round(tax_amount, 2),
            'total': total
        }
        
        has_review = Review.objects.filter(booking=current_booking).exists()
        if has_review:
            review = Review.objects.filter(booking=current_booking).first()
            feedback = review 

    context = {
        'bookings': bookings,
        'today': timezone.now().date(),
        'booking': current_booking,
        'bills': bills,
        'has_review': has_review,
        'review': review,
        'feedback': feedback
    }
    
    return render(request, 'dashboard/guest_dashboard.html', context)

@ensure_csrf_cookie
def verify_2fa(request):
    """Verifies two-factor authentication code."""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        
        if request.method == 'POST':
            code = request.POST.get('code', '').strip()
            stored_code = user.two_factor_code
            
            if not stored_code:
                messages.error(request, 'Verification code expired. Please login again.')
                return redirect('login')
            
            if stored_code == code:
                login(request, user)
                user.two_factor_code = None  
                user.save()
                request.session.pop('user_id', None)
                messages.success(request, 'Successfully verified!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid verification code.')
        
        return render(request, 'registration/verify_2fa.html', {'user': user})
        
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please login again.')
        return redirect('login')

#----------------------------------------admin management----------------------------------------

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def user_management(request):
    """Manages user accounts with filtering and search capabilities."""
    role_filter = request.GET.get('role', 'all')
    search_query = request.GET.get('search', '')
    
    users = User.objects.all()
    
    if role_filter != 'all':
        users = users.filter(role=role_filter)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'current_role': role_filter,
        'search_query': search_query,
        'role_choices': User.ROLE_CHOICES,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'inactive_users': users.filter(is_active=False).count(),
    }
    
    return render(request, 'admin/user_management.html', context)

@login_required
def edit_user(request, user_id):
    """Edits user profile information and role."""
    user_to_edit = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = EditUserForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('user_management')
    else:
        form = EditUserForm(instance=user_to_edit)
    
    return render(request, 'admin/edit_user.html', {
        'form': form,
        'user': user_to_edit
    })

@login_required
def edit_room(request, room_id):
    """Updates room information and settings."""
    room = get_object_or_404(Room, id=room_id)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully!')
            return redirect('room_management')
    else:
        form = RoomForm(instance=room)
    
    return render(request, 'admin/edit_room.html', {
        'form': form,
        'room': room
    })

@login_required
def delete_room(request, room_id):
    """Deletes a room from the system."""
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    return redirect('room_management')

@login_required
def room_management(request):
    """Manages room listings and their statuses."""
    rooms = Room.objects.all()
    return render(request, 'admin/room_management.html', {'rooms': rooms})

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def staff_management(request):
    """Manages staff members with role-based filtering."""
    role_filter = request.GET.get('role', 'all')
    search_query = request.GET.get('search', '')
    
    staff_members = User.objects.exclude(role__in=['admin', 'guest'])
    
    if role_filter != 'all':
        staff_members = staff_members.filter(role=role_filter)
    
    if search_query:
        staff_members = staff_members.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    context = {
        'staff_members': staff_members,
        'current_role': role_filter,
        'search_query': search_query,
        'role_choices': [
            ('manager', 'Managers'),
            ('receptionist', 'Receptionists'),
            ('housekeeping', 'Housekeeping')
        ],
        'total_staff': staff_members.count(),
        'active_staff': staff_members.filter(is_active=True).count(),
        'inactive_staff': staff_members.filter(is_active=False).count(),
    }
    
    return render(request, 'admin/staff_management.html', context)

#----------------------------------------booking----------------------------------------

@login_required
def booking_create(request, room_id):
    """Creates a new booking for a room."""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                check_in_date = form.cleaned_data['check_in_date']
                check_out_date = form.cleaned_data['check_out_date']

                if not room.is_available(check_in_date, check_out_date):
                    messages.error(request, 'Room is not available for the selected dates.')
                    return render(request, 'bookings/booking_form.html', {'form': form, 'room': room})
                
                booking = form.save(commit=False)
                booking.room = room
                booking.guest = request.user

                room.update_status()
                
                nights = (booking.check_out_date - booking.check_in_date).days
                
                base_price = room.category.base_price
                booking.room_charges = base_price * Decimal(str(nights))
                booking.service_charges = Decimal('0')
                booking.tax_amount = (booking.room_charges + booking.service_charges) * Decimal('0.18')
                booking.total_amount = booking.room_charges + booking.service_charges + booking.tax_amount
        
                booking.save()
                messages.success(request, 'Booking created successfully!')
                return redirect('bill_details', booking_id=booking.id)
                
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
                return render(request, 'bookings/booking_form.html', {'form': form, 'room': room})
    else:
        initial_data = {}
        if request.GET.get('check_in') and request.GET.get('check_out'):
            initial_data = {
                'check_in_date': request.GET.get('check_in'),
                'check_out_date': request.GET.get('check_out')
            }
        form = BookingForm(initial=initial_data)
    
    return render(request, 'bookings/booking_form.html', {
        'form': form,
        'room': room,
        'room_price': float(room.category.base_price)
    })

@login_required
def booking_list(request):
    """Lists all bookings based on user role."""
    if request.user.role == User.MANAGER:
        bookings = Booking.objects.all()
    elif request.user.role == User.RECEPTIONIST:
        bookings = Booking.objects.all()
    else:
        bookings = Booking.objects.filter(guest=request.user)
    return render(request, 'bookings/booking_list.html', {'bookings': bookings})


@login_required
def check_out(request, booking_id):
    """Processes guest check-out and updates booking status."""
    booking = get_object_or_404(Booking, id=booking_id)
    payment = Payment.objects.filter(booking=booking).first()
    if request.method == 'POST':
        booking.status = 'CHECKED_OUT'
        booking.save()
        return redirect('booking_list')
    return render(request, 'bookings/check_out.html', {'booking': booking, 'payment': payment})

@login_required
def approve_booking(request, booking_id):
    """Approves a booking by receptionists."""
    if request.user.role != 'receptionist':
        messages.error(request, 'Unauthorized access')
        return redirect('dashboard')
        
    booking = get_object_or_404(Booking, id=booking_id)
    room = booking.room
    
    if room.status == 'AVAILABLE':
        with transaction.atomic():
            room.status = 'RESERVED'
            room.save()
            
            booking.status = 'CONFIRMED'
            booking.save()
            
            send_notification(
                user=booking.guest,
                type='booking_confirmation',
                title='Booking Confirmed',
                message=f'Your booking for Room {room.room_number} has been confirmed.')
            
        messages.success(request, 'Booking approved successfully')
        return redirect('dashboard')
    else:
        if room.status != 'AVAILABLE':
            messages.error(request, f'Room is not available (current status: {room.status})')
        else:
            messages.error(request, f'Booking cannot be approved (current status: {booking.status})')
    
    return redirect('dashboard')

@login_required
def update_room_status(request, room_id):
    """Updates room status (available, occupied, maintenance)."""
    if request.method == 'POST' and request.user.role in ['receptionist', 'manager']:
        room = get_object_or_404(Room, id=room_id)
        new_status = request.POST.get('status')
        
        if new_status in ['AVAILABLE', 'OCCUPIED', 'MAINTENANCE']:
            room.status = new_status
            room.save()
            messages.success(request, f'Room {room.room_number} status updated to {room.get_status_display()}')
        else:
            messages.error(request, 'Invalid status selected')
            
    return redirect('room_list')

@login_required
def cancel_booking(request, booking_id):
    """Cancels a booking by the guest."""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.user != booking.guest:
        messages.error(request, 'You are not authorized to cancel this booking.')
        return redirect('booking_list')
    
    if booking.status != 'CONFIRMED':
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('booking_list')
    
    hours_until_checkin = (booking.check_in_date - timezone.now().date()).days * 24
    if hours_until_checkin < 24:
        messages.error(request, 'Bookings can only be cancelled at least 24 hours before check-in.')
        return redirect('booking_list')
    
    with transaction.atomic():
        booking.status = 'CANCELLED'
        booking.save()
        
        booking.room.status = 'AVAILABLE'
        booking.room.save()
        
        send_notification(
            user=booking.guest,
            type='booking_cancellation',
            title='Booking Cancelled',
            message=f'Your booking for Room {booking.room.room_number} has been cancelled.',
            link=reverse('booking_list')
        )
    
    messages.success(request, 'Your booking has been cancelled successfully.')
    return redirect('booking_list')

@login_required
@user_passes_test(lambda u: u.role == 'receptionist')
def receptionist_booking(request):
    """Handles walk-in bookings created by receptionists."""
    room = Room.objects.filter(status='AVAILABLE').first()
    
    if request.method == 'POST':
        form = ReceptionistBookingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    guest_data = {
                        'first_name': form.cleaned_data['first_name'],
                        'last_name': form.cleaned_data['last_name'],
                        'email': form.cleaned_data['email'],
                        'phone_number': form.cleaned_data['phone_number'],
                        'role': 'guest'
                    }
                    guest, created = User.objects.get_or_create(
                        email=form.cleaned_data['email'],
                        defaults=guest_data
                    )
                    
                    booking = Booking.objects.create(
                        room=room,
                        guest=guest,
                        check_in_date=form.cleaned_data['check_in_date'],
                        check_out_date=form.cleaned_data['check_out_date'],
                        adults=form.cleaned_data['adults'],
                        children=form.cleaned_data['children'],
                        status='CONFIRMED'
                    )
                    
                    nights = (booking.check_out_date - booking.check_in_date).days
                    room_charges = room.category.base_price * nights
                    tax = room_charges * Decimal('0.18')
                    total_amount = room_charges + tax
                    
                    Payment.objects.create(
                        booking=booking,
                        amount=total_amount,
                        payment_method=form.cleaned_data['payment_mode'],
                        payment_date=timezone.now(), 
                        status='COMPLETED'
                    )
                    
                    messages.success(request, 'Booking confirmed successfully!')
                    return redirect('booking_list')
                    
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
                return redirect('receptionist_booking')
    else:
        form = ReceptionistBookingForm()
    
    context = {
        'form': form,
        'room': room,
        'room_price': float(room.category.base_price)
    }
    return render(request, 'bookings/receptionist_booking.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'receptionist')
def check_in(request, booking_id):
    """Processes guest check-in with ID verification and initial payment."""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        form = CheckInForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    check_in = form.save(commit=False)
                    check_in.booking = booking
                    
                    if 'id_proof_document' in request.FILES:
                        file = request.FILES['id_proof_document']
                        ext = file.name.split('.')[-1]
                        filename = f"id_proofs/{booking.guest.id}_{booking.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                        check_in.id_proof_document.save(filename, file, save=False)
                    
                    check_in.save()
                    
                    booking.status = 'CHECKED_IN'
                    booking.save()

                    messages.success(request, 'Check-in completed successfully!')
                    return redirect('booking_list')
                    
            except Exception as e:
                messages.error(request, f'Error during check-in: {str(e)}')
                return redirect('check_in', booking_id=booking_id)
    else:
        form = CheckInForm()
    
    context = {
        'booking': booking,
        'form': form
    }
    return render(request, 'bookings/check_in.html', context)

@login_required
def booking_detail(request, booking_id):
    """Displays detailed information for a specific booking."""
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'bookings/booking_detail.html', {'booking': booking})

#----------------------------------------profile----------------------------------------

@login_required
def profile_view(request):
    """Displays user profile information."""
    form = UserProfileForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': form})

@login_required
def profile_update(request):
    """Updates user profile information."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    return redirect('profile')

@login_required
def toggle_2fa(request):
    """Toggles two-factor authentication for user account."""
    if request.method == 'POST':
        user = request.user
        user.two_factor_enabled = not user.two_factor_enabled
        user.save()
        status = 'enabled' if user.two_factor_enabled else 'disabled'
        messages.success(request, f'Two-factor authentication has been {status}.')
    return redirect('profile')

#----------------------------------------housekeeping----------------------------------------

@login_required
def housekeeping_task_update(request, task_id):
    """Updates the status and details of a housekeeping task."""
    task = HousekeepingTask.objects.get(id=task_id)
    if request.user.role == User.HOUSEKEEPING and task.assigned_to == request.user:
        if request.method == 'POST':
            form = HousekeepingTaskForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                return redirect('dashboard')
        else:
            form = HousekeepingTaskForm(instance=task)
        return render(request, 'task_form.html', {'form': form})
    return redirect('dashboard')

#----------------------------------------room----------------------------------------

@login_required
def room_create(request):
    """Creates a new room."""
    if request.user.role not in [User.ADMIN, User.MANAGER]:
        messages.error(request, 'You do not have permission to create rooms.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Room {room.room_number} created successfully!')
            return redirect('room_list')
    else:
        form = RoomForm()
    
    return render(request, 'rooms/room_form.html', {'form': form}) 

@login_required
def category_create(request):
    """Creates new room categories with pricing."""
    if request.method == 'POST':
        form = RoomCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = RoomCategoryForm()
    return render(request, 'rooms/category_form.html', {'form': form})

@login_required
def room_list(request):
    """Lists all rooms and checks availability for booking dates."""    
    rooms = Room.objects.all()
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    if check_in and check_out:
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
            
            unavailable_rooms = Booking.objects.filter(
                Q(check_in_date__lte=check_out_date) & 
                Q(check_out_date__gte=check_in_date),
                status__in=['PENDING', 'CONFIRMED', 'CHECKED_IN']
            ).values_list('room_id', flat=True)
            
            rooms = rooms.exclude(id__in=unavailable_rooms)
            
            for room in rooms:
                room.is_available_for_dates = True
        except ValueError:
            messages.error(request, 'Invalid date format')
    else:
        for room in rooms:
            room.is_available_for_dates = room.status == 'AVAILABLE'

    return render(request, 'rooms/room_list.html', {
        'rooms': rooms,
        'check_in': check_in,
        'check_out': check_out
    })

def is_admin_or_manager(user):
    """Checks if user has admin or manager role."""
    return user.role in ['admin', 'manager']


#----------------------------------------staff----------------------------------------

@login_required
def add_staff(request):
    """Creates new staff member accounts."""
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('staff_list')
    else:
        form = StaffForm()
    return render(request, 'staff/add_staff.html', {'form': form})

@login_required
@user_passes_test(is_admin_or_manager)
def staff_list(request):
    """Displays list of all staff members."""
    staff_members = User.objects.filter(
        role__in=['receptionist', 'housekeeping']
    ).order_by('role', 'first_name')
    
    return render(request, 'staff/staff_list.html', {
        'staff_members': staff_members
    })

@login_required
def toggle_staff_status(request, staff_id):
    """Toggles active/inactive status of staff members."""
    staff_member = get_object_or_404(User, id=staff_id)
    staff_member.is_active = not staff_member.is_active
    staff_member.save()
    return redirect('staff_list')

@login_required
def assign_duties(request):
    """Assigns housekeeping tasks to staff members."""
    if request.method == 'POST':
        form = AssignDutiesForm(request.POST)
        if form.is_valid():
            task = form.save()
            
            send_notification(
                user=task.assigned_to,
                type='task_assignment',
                title='New Task Assigned',
                message=f'You have been assigned to {task.get_task_type_display()} in Room {task.room.room_number}',
                link=reverse('assign_duties')
            )
            
            messages.success(request, 'Task assigned successfully!')
            return redirect('assign_duties')
    else:
        form = AssignDutiesForm()
    
    current_tasks = HousekeepingTask.objects.filter(
        status__in=['pending', 'in_progress']
    ).order_by('-created_at')
    
    return render(request, 'housekeeping/assign_duties.html', {
        'form': form,
        'current_tasks': current_tasks
    })

@login_required
def update_task_status(request, task_id):
    """Updates housekeeping task completion status."""
    task = HousekeepingTask.objects.get(id=task_id)
    task.status = 'completed'
    task.save()
    return redirect('dashboard')

#----------------------------------------inventory----------------------------------------

@login_required
def inventory_list(request):
    """Displays list of all inventory items."""
    inventory_items = InventoryItem.objects.all()
    return render(request, 'inventory/inventory_list.html', {'inventory_items': inventory_items})


@login_required
@user_passes_test(lambda u: u.role in ['manager', 'housekeeping'])
def inventory_create(request):
    """Creates new inventory items with initial quantity."""
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            inventory_item = form.save()
            messages.success(request, f'Inventory item "{inventory_item.name}" created successfully.')
            return redirect('inventory_list')
    else:
        form = InventoryForm()
    
    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'title': 'Add New Inventory Item',
        'button_text': 'Add Inventory Item'
    })

@login_required
@user_passes_test(lambda u: u.role in ['manager', 'housekeeping'])
def inventory_edit(request, item_id):
    """Edits existing inventory item details."""
    item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            inventory_item = form.save()
            messages.success(request, f'Inventory item "{inventory_item.name}" updated successfully.')
            return redirect('inventory_list')
    else:
        form = InventoryForm(instance=item)
    
    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'title': 'Edit Inventory Item',
        'button_text': 'Update Inventory Item'
    })


@login_required
def request_supplies(request):
    """Handles supply requests from staff members."""
    if request.method == 'POST':
        form = SupplyRequestForm(request.POST)
        if form.is_valid():
            supply_request = form.save(commit=False)
            supply_request.requested_by = request.user
            supply_request.save()
            
            managers = User.objects.filter(role='manager')
            for manager in managers:
                send_notification(
                    user=manager,
                    type='supply_request',
                    title='New Supply Request',
                    message=f'New supply request from {request.user.get_full_name()}'
                )
            
            messages.success(request, 'Supply request submitted successfully')
            return redirect('dashboard')
    else:
        form = SupplyRequestForm()
    
    context = {
        'form': form,
        'pending_requests': SupplyRequest.objects.filter(
            requested_by=request.user,
            status='pending'
        ).order_by('-created_at')
    }
    return render(request, 'housekeeping/request_supplies.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'manager')
def process_supply_request(request, request_id):
    """Processes and approves/rejects supply requests."""
    supply_request = get_object_or_404(SupplyRequest, id=request_id)
    action = request.POST.get('action')
    
    if action in ['approve', 'reject']:
        with transaction.atomic():
            supply_request.status = 'approved' if action == 'approve' else 'rejected'
            supply_request.processed_by = request.user
            supply_request.processed_at = timezone.now()
            supply_request.save()
            
            if action == 'approve':
                supply = supply_request.supply
                supply.quantity += supply_request.quantity
                supply.save()
            
            send_notification(
                user=supply_request.requested_by,
                type='supply_request_processed',
                title=f'Supply Request {supply_request.status.title()}',
                message=f'Your supply request has been {supply_request.status}',
                link=reverse('request_supplies')
            )
            
            messages.success(request, f'Supply request {supply_request.status} successfully')
    
    return redirect('manager_dashboard')

@login_required
@user_passes_test(lambda u: u.role == 'housekeeping')
def spend_supplies(request):
    """Records usage of supplies by housekeeping staff."""
    if request.method == 'POST':
        try:
            supply_id = request.POST.get('supply_id')
            quantity = request.POST.get('quantity')
            reason = request.POST.get('reason')
            
            if not all([supply_id, quantity, reason]):
                messages.error(request, 'All fields are required.')
                return redirect('dashboard')
            
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    messages.error(request, 'Quantity must be greater than 0.')
                    return redirect('dashboard')
            except ValueError:
                messages.error(request, 'Invalid quantity value.')
                return redirect('dashboard')
            
            supply = InventoryItem.objects.get(id=supply_id)
            
            if quantity > supply.quantity:
                messages.error(request, f'Not enough {supply.name} in stock. Available: {supply.quantity}')
                return redirect('dashboard')
            
            with transaction.atomic():
                supply.quantity -= quantity
                supply.save()
                
                SupplyUsage.objects.create(
                    supply=supply,
                    quantity=quantity,
                    used_by=request.user,
                    reason=reason
                )
                
                messages.success(request, f'Successfully used {quantity} {supply.name}')
                
        except InventoryItem.DoesNotExist:
            messages.error(request, 'Selected supply not found.')
        except Exception as e:
            messages.error(request, str(e))
    
    return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.role in ['manager', 'housekeeping'])
def restock_item(request, item_id):
    """Restocks inventory items with new quantities."""
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 0))
            if quantity <= 0:
                messages.error(request, 'Quantity must be greater than 0')
                return redirect('inventory_list')
            
            with transaction.atomic():
                item = get_object_or_404(InventoryItem, id=item_id)
                item.quantity += quantity
                item.last_restocked = timezone.now()
                item.save()
                
                messages.success(request, f'Successfully added {quantity} {item.unit}s of {item.name}')
                
        except ValueError:
            messages.error(request, 'Invalid quantity provided')
        except Exception as e:
            messages.error(request, 'Error restocking item')
            
    return redirect('inventory_list')

#----------------------------------------review----------------------------------------

@login_required
def create_review(request, booking_id):
    """Creates a review for a completed booking."""
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    
    existing_review = Review.objects.filter(booking=booking).first()
    if existing_review:
        messages.error(request, 'You have already submitted a review for this booking.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            cleanliness_rating = int(request.POST.get('cleanliness_rating', 0))
            staff_rating = int(request.POST.get('staff_rating', 0))
            food_rating = int(request.POST.get('food_rating', 0))
            overall_rating = int(request.POST.get('overall_rating', 0))
            feedback = request.POST.get('feedback', '').strip()
            
            if not all([1 <= rating <= 5 for rating in [cleanliness_rating, staff_rating, food_rating, overall_rating]]):
                messages.error(request, 'Please provide all ratings between 1 and 5.')
                return render(request, 'reviews/review_form.html', {'booking': booking})
            
            review = Review.objects.create(
                booking=booking,
                guest=request.user,
                cleanliness_rating=cleanliness_rating,
                staff_rating=staff_rating,
                food_rating=food_rating,
                overall_rating=overall_rating,
                feedback=feedback
            )
            
            messages.success(request, 'Thank you for your detailed review!')
            return redirect('dashboard')
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid rating values provided.')
            return render(request, 'reviews/review_form.html', {'booking': booking})
    
    return render(request, 'reviews/review_form.html', {
        'booking': booking
    })

@login_required
def review_list(request):
    """Displays list of all reviews with average ratings."""
    reviews = Review.objects.all().order_by('-created_at')

    averages = Review.objects.aggregate(
        avg_rating=Avg('overall_rating'),
        avg_cleanliness=Avg('cleanliness_rating'),
        avg_staff=Avg('staff_rating'),
        avg_food=Avg('food_rating')
    )
    
    context = {
        'reviews': reviews,
        'avg_rating': averages['avg_rating'] or 0,
        'avg_cleanliness': averages['avg_cleanliness'] or 0,
        'avg_staff': averages['avg_staff'] or 0,
        'avg_food': averages['avg_food'] or 0,
    }
    return render(request, 'reviews/review_list.html', context)

@login_required
def delete_review(request, booking_id):
    """Deletes a user's review for a specific booking."""
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    review = get_object_or_404(Review, booking=booking)
    review.delete()
    messages.success(request, 'Review deleted successfully.')
    return redirect('dashboard')

#----------------------------------------notification----------------------------------------

@login_required
def notifications_list(request):
    """Displays list of user notifications with read/unread status."""
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    return render(request, 'notifications/notification_list.html', context)

def send_notification(user, type, title, message, link=None):
    notification = Notification.objects.create(
        user=user,
        type=type,
        title=title,
        message=message,
        link=link
    )
    
    if type in ['booking_confirmation', 'check_in_reminder', 'promotional']:
        email_template = f'notifications/email/{type}.html'
        email_content = render_to_string(email_template, {
            'user': user,
            'message': message,
            'link': link
        })
        
        send_mail(
            subject=title,
            message='',
            html_message=email_content,
            from_email='noreply@hms.com',
            recipient_list=[user.email],
        )
    
    return notification

#----------------------------------------bill & payment----------------------------------------

@login_required
def bill_details(request, booking_id):
    """Generates detailed bill information for a specific booking."""
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user != booking.guest and not request.user.is_staff:
        messages.error(request, 'You are not authorized to view this bill.')
        return redirect('dashboard')
    
    total_nights = (booking.check_out_date - booking.check_in_date).days
    
    room_charges = round(booking.room.category.base_price * total_nights, 2)
    
    # Simplified service charges calculation using the stored value
    service_charges = booking.service_charges
    
    tax_rate = Decimal('0.18')
    room_tax = round(room_charges * tax_rate, 2)
    total_amount = round(room_charges + room_tax + service_charges, 2)
    
    payments = Payment.objects.filter(booking=booking).order_by('-payment_date')
    total_paid = round(sum(payment.amount for payment in payments), 2)
    
    context = {
        'booking': booking,
        'bill_details': {
            'total_nights': total_nights,
            'room_charges': room_charges,
            'room_tax': room_tax,
            'tax_rate': int(tax_rate * 100),
            'service_charges': service_charges,
            'tax_amount': room_tax,
            'total_amount': total_amount,
            'total_paid': total_paid,
            'balance': round(total_amount - total_paid, 2)
        },
        'payments': payments,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    }
    
    return render(request, 'bookings/bill_details.html', context)

@require_POST
def verify_payment(request):
    """Verifies payment details and updates booking status."""
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        payment_id = data.get('payment_id')
        amount = data.get('amount')
        
        booking = get_object_or_404(Booking, id=booking_id)
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        Payment.objects.create(
            booking=booking,
            amount=amount,
            payment_method='RAZORPAY',
            transaction_id=payment_id,
            status='SUCCESS'
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def process_cash_payment(request, booking_id):
    """Processes cash payments for bookings."""
    booking = get_object_or_404(Booking, id=booking_id)
    if not request.user.is_staff:
        messages.error(request, 'Only staff members can process cash payments.')
        return redirect('bill_details', booking_id=booking_id)
    
    try:
        amount = Decimal(request.POST.get('amount'))
        
        Payment.objects.create(
            booking=booking,
            amount=amount,
            payment_method='CASH',
            status='SUCCESS'
        )
        
        messages.success(request, f'Cash payment of ₹{amount:.2f} processed successfully.')
    except Exception as e:
        messages.error(request, f'Failed to process payment: {str(e)}')
    
    return redirect('bill_details', booking_id=booking_id)

#----------------------------------------report----------------------------------------

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'manager'])
def generate_reports(request):
    """Generates reports for operational statistics."""
    try:
        today = timezone.now().date()
        start_date = request.GET.get('from_date', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.GET.get('to_date', today.strftime('%Y-%m-%d'))
        
        start_datetime = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
        end_datetime = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)) - timedelta(seconds=1)
        
        context = {
            'from_date': start_datetime.date(),
            'to_date': end_datetime.date(),
            'revenue': get_revenue_data(start_datetime, end_datetime),
            'occupancy': get_occupancy_data(start_datetime.date(), end_datetime.date()),
            'staff': get_staff_data(start_datetime, end_datetime),
            'trends': get_booking_data(start_datetime, end_datetime)
        }
        
        return render(request, 'reports/reports.html', context)
        
    except Exception as e:
        messages.error(request, f"Error generating reports: {str(e)}")
        return redirect('dashboard')

def get_revenue_data(start_datetime, end_datetime):
    """Calculate basic revenue metrics"""
    payments = Payment.objects.filter(
        payment_date__range=[start_datetime, end_datetime],
        status='SUCCESS'
    )
    
    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
    payment_methods = payments.values('payment_method').annotate(
        total=Sum('amount')
    )
    
    return {
        'total_revenue': round(total_revenue, 2),
        'payment_methods': {
            p['payment_method']: round(p['total'], 2) 
            for p in payment_methods
        }
    }

def get_occupancy_data(start_date, end_date):
    """Calculate room occupancy metrics"""
    total_rooms = Room.objects.count()
    
    bookings = Booking.objects.filter(
        check_in_date__lte=end_date,
        check_out_date__gte=start_date,
        status__in=['CONFIRMED', 'CHECKED_IN']
    )
    
    # Calculate occupancy percentage and peak data
    days_in_range = (end_date - start_date).days + 1
    total_possible_days = total_rooms * days_in_range
    occupied_days = bookings.count() * days_in_range
    
    popular_categories = bookings.values(
        'room__category__name'
    ).annotate(
        total_bookings=Count('id')
    ).order_by('-total_bookings')
    
    peak_date = start_date 
    peak_occupancy = bookings.count()  
    
    return {
        'average_occupancy': round((occupied_days / total_possible_days * 100), 2) if total_possible_days > 0 else 0,
        'peak_date': peak_date,
        'peak_occupancy': peak_occupancy,
        'popular_categories': popular_categories,
        'total_rooms': total_rooms
    }

def get_staff_data(start_datetime, end_datetime):
    """Calculate staff performance metrics"""
    tasks = HousekeepingTask.objects.filter(
        created_at__range=[start_datetime, end_datetime]
    )
    
    completed_tasks = tasks.filter(status='completed')
    
    supply_usage = SupplyUsage.objects.filter(
        usage_date__range=[start_datetime, end_datetime]
    ).values(
        'supply__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')
    
    return {
        'task_statistics': {
            'total_tasks': tasks.count(),
            'completed_tasks': completed_tasks.count()
        },
        'supply_usage': supply_usage
    }

def get_booking_data(start_datetime, end_datetime):
    """Calculate booking trends and review metrics"""
    bookings = Booking.objects.filter(
        created_at__range=[start_datetime, end_datetime]
    )
    
    avg_stay = bookings.aggregate(
        avg_duration=Avg(F('check_out_date') - F('check_in_date'))
    )['avg_duration']
    
    status_breakdown = bookings.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    reviews = Review.objects.filter(
        created_at__range=[start_datetime, end_datetime]
    )
    
    ratings = reviews.aggregate(
        cleanliness=Avg('cleanliness_rating'),
        staff=Avg('staff_rating'),
        food=Avg('food_rating'),
        overall=Avg('overall_rating')
    )
    
    return {
        'booking_statistics': {
            'total_bookings': bookings.count(),
            'avg_stay_duration': avg_stay or timedelta(days=0),
            'status_breakdown': status_breakdown
        },
        'ratings': {
            key: round(value or 0, 2)
            for key, value in ratings.items()
        }
    }

#----------------------------------------payroll----------------------------------------

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'manager'])
def payroll_summary(request):
    """Displays payroll summary for admin and manager."""
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
        
    try:
        today = timezone.now().date()
        start_date = request.GET.get('from_date', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.GET.get('to_date', today.strftime('%Y-%m-%d'))
        current_role = request.GET.get('role', 'all')
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        staff_queryset = User.objects.exclude(role__in=['admin', 'guest'])
        
        if current_role != 'all':
            staff_queryset = staff_queryset.filter(role=current_role)
        
        payroll_records = []
        total_payroll = Decimal('0.00')
        pending_payments = 0
        
        base_rates = {
            'manager': Decimal('500.00'),
            'receptionist': Decimal('300.00'),
            'housekeeping': Decimal('200.00')
        }
        
        standard_hours = {
            'manager': 160, 
            'receptionist': 180,  
            'housekeeping': 200   
        }
        
        standard_shifts = {
            'manager': 20,        
            'receptionist': 20,  
            'housekeeping': 20   
        }
        
        for staff in staff_queryset:
            hours_worked = standard_hours.get(staff.role, 0)
            shifts_completed = standard_shifts.get(staff.role, 0)
            hourly_rate = base_rates.get(staff.role, Decimal('0.00'))
            
            base_pay = hourly_rate * Decimal(hours_worked)
            bonus = Decimal('1000.00') 
            total_pay = base_pay + bonus
            
            record, created = PayrollRecord.objects.get_or_create(
                staff=staff,
                period_start=start_date,
                period_end=end_date,
                defaults={
                    'hours_worked': hours_worked,
                    'shifts_completed': shifts_completed,
                    'base_pay': base_pay,
                    'bonus': bonus,
                    'total_pay': total_pay
                }
            )
            
            if not created:
                record.hours_worked = hours_worked
                record.shifts_completed = shifts_completed
                record.base_pay = base_pay
                record.bonus = bonus
                record.total_pay = total_pay
                record.save()
            
            payroll_records.append(record)
            total_payroll += total_pay
            if record.status == 'PENDING':
                pending_payments += 1
        
        context = {
            'payroll_records': payroll_records,
            'total_payroll': total_payroll,
            'pending_payments': pending_payments,
            'total_staff': staff_queryset.count(),
            'current_role': current_role,
            'roles': User.ROLE_CHOICES[1:4],  
            'from_date': start_date,
            'to_date': end_date
        }
        
        return render(request, 'admin/payroll_summary.html', context)
        
    except Exception as e:
        messages.error(request, f"Error generating payroll: {str(e)}")
        return redirect('dashboard')

@login_required
def approve_payroll(request, record_id):
    """Approves payroll for a specific record and notifies the staff member."""
    try:
        record = get_object_or_404(PayrollRecord, id=record_id)
        record.status = 'APPROVED'
        record.save()

        send_notification(
            user=record.staff,
            type='payroll_approval',
            title='Payroll Approved',
            message=f'Your payroll for period {record.period_start.strftime("%d %b")} to {record.period_end.strftime("%d %b")} has been approved. Total amount: ₹{record.total_pay}',
            link=reverse('payroll_summary')
        )
        
        messages.success(request, 'Payroll approved successfully')
    except Exception as e:
        messages.error(request, f'Error approving payroll: {str(e)}')
    
    return redirect('payroll_summary')

@login_required
def generate_payroll(request):
    """Generates payroll for all staff members."""
    try:
        messages.success(request, 'Payroll generated successfully')
    except Exception as e:
        messages.error(request, f'Error generating payroll: {str(e)}')
    
    return redirect('payroll_summary')
