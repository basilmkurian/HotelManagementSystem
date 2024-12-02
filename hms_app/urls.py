from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Password reset paths
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    #----------------------------------------profile----------------------------------------
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/toggle-2fa/', views.toggle_2fa, name='toggle_2fa'),
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),

    #----------------------------------------room----------------------------------------
    path('rooms/create/', views.room_create, name='room_create'),
    path('categories/create/', views.category_create, name='category_create'),
    path('rooms/list/', views.room_list, name='room_list'),
    path('room-management/', views.room_management, name='room_management'),
    path('delete-room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('update-room-status/<int:room_id>/', views.update_room_status, name='update_room_status'),

    #----------------------------------------staff----------------------------------------
    path('staff/list/', views.staff_list, name='staff_list'),
    path('staff/<int:staff_id>/toggle-status/', views.toggle_staff_status, name='toggle_staff_status'),
    path('assign-duties/', views.assign_duties, name='assign_duties'),
    path('add-staff/', views.add_staff, name='add_staff'),
    path('staff-management/', views.staff_management, name='staff_management'),

    #----------------------------------------inventory----------------------------------------
    path('inventory/list/', views.inventory_list, name='inventory_list'),
    path('inventory/create/', views.inventory_create, name='inventory_create'),
    path('spend-supplies/', views.spend_supplies, name='spend_supplies'),
    path('inventory/restock/<int:item_id>/', views.restock_item, name='restock_item'),
    path('request-supplies/', views.request_supplies, name='request_supplies'),
    path('inventory/edit/<int:item_id>/', views.inventory_edit, name='inventory_edit'),

    #----------------------------------------booking----------------------------------------
    path('bookings/create/<int:room_id>/', views.booking_create, name='booking_create'),
    path('bookings/list/', views.booking_list, name='booking_list'),
    path('check-in/<int:booking_id>/', views.check_in, name='check_in'),
    path('check-out/<int:booking_id>/', views.check_out, name='check_out'),
    path('receptionist-booking/', views.receptionist_booking, name='receptionist_booking'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('approve-booking/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    
    #----------------------------------------user----------------------------------------
    path('user-management/', views.user_management, name='user_management'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('edit-room/<int:room_id>/', views.edit_room, name='edit_room'),
    
    #----------------------------------------review----------------------------------------
    path('review/create/<int:booking_id>/', views.create_review, name='create_review'),
    path('booking/<int:booking_id>/review/', views.create_review, name='create_review'),
    path('reviews/list/', views.review_list, name='review_list'),
    path('review/<int:booking_id>/delete/', views.delete_review, name='delete_review'),
    
    #----------------------------------------billing----------------------------------------
    path('booking/<int:booking_id>/bill/', views.bill_details, name='bill_details'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('bookings/<int:booking_id>/process-cash-payment/', views.process_cash_payment, name='process_cash_payment'),
    
    #----------------------------------------payroll----------------------------------------
    path('payroll/', views.payroll_summary, name='payroll_summary'),
    path('payroll/approve/<int:record_id>/', views.approve_payroll, name='approve_payroll'),
    path('payroll/generate/', views.generate_payroll, name='generate_payroll'),

    #----------------------------------------reports----------------------------------------
    path('reports/', views.generate_reports, name='generate_reports'),
    path('update-task-status/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('notifications/list/', views.notifications_list, name='notifications_list'),
] 