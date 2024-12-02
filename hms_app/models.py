from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models import Q


class User(AbstractUser):
    ADMIN = 'admin'
    MANAGER = 'manager'
    RECEPTIONIST = 'receptionist'
    HOUSEKEEPING = 'housekeeping'
    GUEST = 'guest'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (RECEPTIONIST, 'Receptionist'),
        (HOUSEKEEPING, 'Housekeeping'),
        (GUEST, 'Guest'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=GUEST)
    phone_number = models.CharField(max_length=15, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_code = models.CharField(max_length=6, null=True, blank=True)
    
class RoomCategory(models.Model):
    name = models.CharField(max_length=50)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Room Categories"

class Room(models.Model):
    ROOM_STATUS = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('MAINTENANCE', 'Under Maintenance')
    ]

    room_number = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey(RoomCategory, on_delete=models.PROTECT, related_name='rooms', null=True, blank=True)
    max_occupancy = models.PositiveIntegerField(default=2)
    bed_count = models.PositiveIntegerField(default=1)
    has_wifi = models.BooleanField(default=True)
    has_ac = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default='AVAILABLE')
    image = models.ImageField(upload_to='room_images/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.room_number}"

    class Meta:
        ordering = ['room_number']

    def is_available(self, check_in_date, check_out_date):
        overlapping_bookings = self.booking_set.filter(
            Q(check_in_date__lte=check_out_date) & 
            Q(check_out_date__gte=check_in_date),
            status__in=['PENDING', 'CONFIRMED', 'CHECKED_IN']
        ).exists()
        
        return not overlapping_bookings and self.status == 'AVAILABLE'

    def update_status(self):
        today = timezone.now().date()
        current_booking = self.booking_set.filter(
            check_in_date__lte=today,
            check_out_date__gte=today,
            status__in=['CONFIRMED', 'CHECKED_IN']
        ).first()
        
        if current_booking:
            if current_booking.status == 'CHECKED_IN':
                self.status = 'OCCUPIED'
            else:
                self.status = 'RESERVED'
        else:
            if self.status != 'MAINTENANCE':
                self.status = 'AVAILABLE'
        
        self.save()
        
    def is_available(self, check_in_date, check_out_date):
        if self.status == 'MAINTENANCE':
            return False
            
        overlapping_bookings = self.booking_set.filter(
            Q(check_in_date__lte=check_out_date) & 
            Q(check_out_date__gte=check_in_date),
            status__in=['PENDING', 'CONFIRMED', 'CHECKED_IN']
        ).exists()
        
        return not overlapping_bookings

class Booking(models.Model):
    BOOKING_SOURCE_CHOICES = [
        ('DIRECT', 'Direct'),
        ('ONLINE', 'Online'),
    ]

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked In'),
        ('CHECKED_OUT', 'Checked Out'),
        ('CANCELLED', 'Cancelled'),
    )

    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    guest = models.ForeignKey('User', on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    booking_source = models.CharField(max_length=20, choices=BOOKING_SOURCE_CHOICES, default='DIRECT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Payment fields
    room_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partial'),
        ('PAID', 'Paid')
    ], default='PENDING')

    def save(self, *args, **kwargs):
        if not self.total_amount: 
            nights = (self.check_out_date - self.check_in_date).days
            
            room_price = self.room.category.base_price
            total_nights = Decimal(str(nights))
            
            self.room_charges = room_price * total_nights
            self.service_charges = Decimal('0') 
            self.tax_amount = (self.room_charges + self.service_charges) * Decimal('0.18')
            self.total_amount = self.room_charges + self.service_charges + self.tax_amount
            
        super().save(*args, **kwargs)


class HousekeepingTask(models.Model):
    TASK_TYPES = [
        ('cleaning', 'Room Cleaning'),
        ('maintenance', 'Maintenance'),
        ('laundry', 'Laundry'),
        ('supplies', 'Restock Supplies')
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    def get_default_staff():
        User = get_user_model()
        default_staff = User.objects.filter(role='housekeeping', is_active=True).first()
        if default_staff:
            return default_staff.id
        return None

    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey('User', on_delete=models.CASCADE, default=get_default_staff)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='cleaning')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('cleaning', 'Cleaning Supplies'),
        ('amenities', 'Guest Amenities'),
        ('linens', 'Linens'),
        ('maintenance', 'Maintenance'),
        ('office', 'Office Supplies')
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='cleaning')
    quantity = models.PositiveIntegerField(default=0)
    minimum_threshold = models.PositiveIntegerField(default=10)
    unit = models.CharField(max_length=20, default='pieces')  
    description = models.TextField(blank=True, null=True)  
    last_restocked = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name


class Review(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    guest = models.ForeignKey('User', on_delete=models.CASCADE, default=None)
    cleanliness_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rate cleanliness from 1-5",
        default=3
    )
    staff_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rate staff behavior from 1-5",
        default=3
    )
    food_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rate food quality from 1-5",
        default=3
    )
    overall_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Overall rating from 1-5",
        default=3
    )
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def average_rating(self):
        return (self.cleanliness_rating + self.staff_rating + 
                self.food_rating + self.overall_rating) / 4.0

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('booking_confirmation', 'Booking Confirmation'),
        ('booking_cancellation', 'Booking Cancellation'),
        ('low_inventory', 'Low Inventory Alert'),
        ('maintenance', 'Maintenance Alert'),
        ('check_in_reminder', 'Check-in Reminder'),
        ('check_out_reminder', 'Check-out Reminder'),
        ('promotional', 'Promotional Offer'),
        ('feedback_request', 'Feedback Request'),
    )

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

class CheckIn(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    check_in_time = models.DateTimeField(auto_now_add=True)
    id_type = models.CharField(max_length=20)
    id_number = models.CharField(max_length=50)
    id_proof_document = models.FileField(upload_to='id_proofs/')
    payment_mode = models.CharField(max_length=20)
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2)
    additional_services = models.JSONField(default=list)
    
    def __str__(self):
        return f"Check-in for {self.booking.guest.get_full_name()} - Room {self.booking.room.room_number}"

class SupplyRequest(models.Model):
    URGENCY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    supply = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supply_requests')
    quantity = models.PositiveIntegerField()
    urgency = models.CharField(max_length=20, choices=URGENCY_LEVELS, default='medium')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='processed_requests'
    )


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('UPI', 'UPI'),
        ('WALLET', 'Digital Wallet')
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='SUCCESS')

class SupplyUsage(models.Model):
    supply = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    used_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    usage_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.supply.name} - {self.quantity} used by {self.used_by.get_full_name()}"

class PayrollRecord(models.Model):
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid')
    ]
    
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payroll_records')
    period_start = models.DateField()
    period_end = models.DateField()
    hours_worked = models.DecimalField(max_digits=10, decimal_places=2)
    shifts_completed = models.IntegerField()
    base_pay = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2)
    total_pay = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_status_display(self):
        return dict(self.PAYMENT_STATUS)[self.status]

