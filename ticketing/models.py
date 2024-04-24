from django.contrib.auth.models import AbstractUser
from django.db import models
from io import BytesIO


class CustomUser(AbstractUser):
    # Add any additional fields or methods here
    pass


class Ticket(models.Model):
    ticket_id = models.IntegerField()
    used = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.ticket_id}"


class Order(models.Model):
    ticket_number = models.IntegerField()
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    email = models.EmailField()
    isPaid = models.BooleanField(default=False)
    ticket_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} - {self.user.username} - {self.ticket.ticket_id}"
