from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Booking, HousekeepingTask, Room, RoomCategory, InventoryItem, Review, CheckIn, SupplyRequest
from django.core.exceptions import ValidationError
from datetime import date
from django.utils import timezone

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your last name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your email'
        })
    )
    
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your phone number'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Choose a username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm your password'
        })

class TwoFactorVerificationForm(forms.Form):
    code = forms.CharField(max_length=6, required=True)

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in_date', 'check_out_date', 'adults', 'children']
        widgets = {
            'check_in_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border rounded-lg',
                'required': True
            }),
            'check_out_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border rounded-lg',
                'required': True
            }),
            'adults': forms.NumberInput(attrs={
                'min': 1,
                'max': 4,
                'class': 'w-full px-3 py-2 border rounded-lg',
                'required': True
            }),
            'children': forms.NumberInput(attrs={
                'min': 0,
                'max': 4,
                'class': 'w-full px-3 py-2 border rounded-lg',
                'required': True
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in_date')
        check_out = cleaned_data.get('check_out_date')
        adults = cleaned_data.get('adults')
        
        if not check_in or not check_out:
            raise ValidationError('Both check-in and check-out dates are required')
            
        if check_in < date.today():
            raise ValidationError({'check_in_date': 'Check-in date cannot be in the past'})
            
        if check_out <= check_in:
            raise ValidationError({'check_out_date': 'Check-out date must be after check-in date'})
        
        if not adults or adults < 1:
            raise ValidationError({'adults': 'At least one adult is required'})
            
        return cleaned_data

class HousekeepingTaskForm(forms.ModelForm):
    class Meta:
        model = HousekeepingTask
        fields = ['assigned_to', 'room', 'task_type', 'priority', 'notes']
        widgets = {
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'room': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'task_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(role='housekeeping', is_active=True)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
        } 

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'category', 'max_occupancy', 'bed_count', 
                 'has_wifi', 'has_ac', 'status', 'image']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'max_occupancy': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'bed_count': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'has_wifi': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600'}),
            'has_ac': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'image': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'accept': 'image/*'}),
        } 

class RoomCategoryForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter category name'
        })
    )
    
    base_price = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter base price',
            'min': '0',
            'step': '0.01'
        })
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter category description',
            'rows': 3
        })
    )

    class Meta:
        model = RoomCategory
        fields = ['name', 'base_price', 'description']

class AssignDutiesForm(forms.ModelForm):
    class Meta:
        model = HousekeepingTask
        fields = ['assigned_to', 'room', 'task_type', 'priority', 'notes']
        widgets = {
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'room': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'task_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(role='housekeeping', is_active=True)

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'quantity', 'minimum_threshold', 'category']


class CheckInForm(forms.ModelForm):
    ID_TYPES = [
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
        ('national_id', 'National ID'),
        ('other', 'Other')
    ]
    
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('bank_transfer', 'Bank Transfer')
    ]
    
    id_type = forms.ChoiceField(
        choices=ID_TYPES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'required': True
        })
    )
    
    id_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter ID number',
            'required': True
        })
    )
    
    id_proof_document = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'required': True
        })
    )
    
    payment_mode = forms.ChoiceField(
        choices=PAYMENT_MODES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'required': True
        })
    )
    
    advance_payment = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter advance amount',
            'required': True,
            'step': '0.01'
        })
    )
    
    additional_services = forms.MultipleChoiceField(
        choices=[
            ('breakfast', 'Breakfast'),
            ('parking', 'Parking'),
            ('wifi', 'WiFi'),
            ('laundry', 'Laundry')
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        }),
        required=False
    )
    
    class Meta:
        model = CheckIn
        fields = ['id_type', 'id_number', 'id_proof_document', 
                 'payment_mode', 'advance_payment', 'additional_services']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
    
class StaffRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'role', 'password1', 'password2']


class StaffForm(UserCreationForm):
    STAFF_ROLES = [
        ('receptionist', 'Receptionist'),
        ('housekeeping', 'Housekeeping'),
        ('manager', 'Manager')
    ]
    
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    role = forms.ChoiceField(
        choices=STAFF_ROLES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'password1', 'password2', 'role']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })

class SupplyRequestForm(forms.ModelForm):
    class Meta:
        model = SupplyRequest
        fields = ['supply', 'quantity', 'urgency', 'notes']
        widgets = {
            'supply': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': 1
            }),
            'urgency': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3
            })
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'category', 'quantity', 'minimum_threshold', 'unit', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': 0
            }),
            'minimum_threshold': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': 0
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3
            })
        }

class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            })
        }

class ReceptionistBookingForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter guest first name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter guest last name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter guest email'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter guest phone number'
        })
    )
    check_in_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'required': True
        })
    )
    check_out_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'required': True
        })
    )
    adults = forms.IntegerField(
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'required': True,
            'placeholder': 'Number of adults'
        })
    )
    children = forms.IntegerField(
        min_value=0,
        max_value=10,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Number of children'
        })
    )
    payment_mode = forms.ChoiceField(
        choices=[
            ('CASH', 'Cash'),
            ('CARD', 'Card'),
            ('UPI', 'UPI')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        
        if check_in_date and check_out_date:
            if check_in_date < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past")
            
            if check_out_date <= check_in_date:
                raise ValidationError("Check-out date must be after check-in date")
            
        return cleaned_data