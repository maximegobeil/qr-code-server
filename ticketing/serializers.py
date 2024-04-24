from rest_framework import serializers
from .models import CustomUser, Ticket, Order


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'

    def create(self, validated_data):
        ticket = Ticket.objects.create(**validated_data)
        return ticket


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'ticket_number', 'firstName',
                  'lastName', 'email', 'isPaid', 'ticket_id', 'created_at']

        extra_kwargs = {'ticket_id': {'required': False}}
