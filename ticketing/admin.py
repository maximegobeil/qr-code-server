from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Ticket

# Register your models here.


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Customize the user admin interface if needed
    pass


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'used', 'created_at')
    list_filter = ('used', 'created_at')
    search_fields = ('ticket_id',)
