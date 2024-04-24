from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Ticket, Order
from .serializers import OrderSerializer
import jwt
import os
from dotenv import load_dotenv
import qrcode
from PIL import Image
from django.core.mail import send_mail
from django.db import transaction
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


load_dotenv()
secret = os.getenv('SECRET_KEY')
current_directory = os.path.dirname(os.path.realpath(__file__))


class ValidateTicket(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        jwt_token = request.data.get('jwt')
        print(jwt_token)

        try:

            # Decode JWT token
            decoded_token = jwt.decode(
                jwt_token, secret, algorithms=['HS256'])
            ticket_id = decoded_token['ticket_id']
            print(ticket_id)

            # Retrieve ticket from database
            ticket = Ticket.objects.get(ticket_id=ticket_id)

            if ticket.used:
                print('Ticket already used')
                return Response({'message': 'Ticket already used'}, status=status.HTTP_400_BAD_REQUEST)

            # Mark ticket as used
            ticket.used = True
            ticket.save()

            return Response({'message': 'Ticket validated successfully'}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            # If the token is expired, return an unauthorized response
            print('JWT token expired')
            return Response({'message': 'JWT token expired'}, status=status.HTTP_401_UNAUTHORIZED)

        except jwt.DecodeError:
            print('Invalid JWT token')
            # If the token is invalid (e.g., malformed or tampered with), return an unauthorized response
            return Response({'message': 'Invalid JWT token'}, status=status.HTTP_401_UNAUTHORIZED)

        except Ticket.DoesNotExist:
            print('Ticket not found')
            return Response({'message': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)


class InvalidateTicket(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        jwt_token = request.data.get('jwt')

        try:
            # Decode JWT token
            decoded_token = jwt.decode(
                jwt_token, secret, algorithms=['HS256'])
            ticket_id = decoded_token['ticket_id']

            # Retrieve ticket from database
            ticket = Ticket.objects.get(ticket_id=ticket_id)

            if not ticket.used:
                print('Ticket already unused')
                return Response({'message': 'Ticket already unused'}, status=status.HTTP_400_BAD_REQUEST)

            # Mark ticket as unused
            ticket.used = False
            ticket.save()

            return Response({'message': 'Ticket invalidated successfully'}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            print('JWT token expired')
            return Response({'message': 'JWT token expired'}, status=status.HTTP_401_UNAUTHORIZED)

        except jwt.DecodeError:
            print('Invalid JWT token')
            return Response({'message': 'Invalid JWT token'}, status=status.HTTP_401_UNAUTHORIZED)

        except Ticket.DoesNotExist:
            print('Ticket not found')
            return Response({'message': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)


class CreateOrderAPIView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def perform_create(self, serializer):
        instance = serializer.save()

        # Load HTML template for email
        html_message = render_to_string('confirm_order_email.html', {
                                        'name': instance.firstName, 'nb': instance.ticket_number, 'total_amount': 60 * (instance.ticket_number // 4) + 20 * (instance.ticket_number % 4)})

        # Strip HTML tags for plain text version
        plain_message = strip_tags(html_message)

        # Send the email using send_mail() with the HTML content
        send_mail(
            subject='Les Productions 725 - Confirmation de commande',
            message=plain_message,  # Plain text message
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[instance.email],
            html_message=html_message,  # HTML content for the email body
        )


class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.all()


class UpdateOrderAPIView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            # Update the order to indicate payment
            serializer.save(isPaid=True)

            # Retrieve the number of tickets associated with the order
            ticket_number = instance.ticket_number

            # Retrieve available tickets
            available_tickets = Ticket.objects.filter(
                used=False, sent=False)[:ticket_number]

            if len(available_tickets) < ticket_number:
                # Handle case where there are not enough available tickets
                # You can raise an exception or handle the error as needed
                # For simplicity, let's assume all tickets must be available
                raise Exception("Not enough available tickets")

            # Extract ticket IDs
            ticket_ids = [str(ticket.ticket_id)
                          for ticket in available_tickets]

            # Join ticket IDs with commas and update the order's ticket_id field
            instance.ticket_id = ','.join(ticket_ids)
            instance.save()

            # Send confirmation email
            email = instance.email
            subject = 'Les Productions 725 - Vos Billet(s)'

            # Load HTML template for email
            html_message = render_to_string('send_ticket_email.html', {
                                            'name': instance.firstName, 'total_amount': 60 * (ticket_number // 4) + 20 * (ticket_number % 4), 'nb': ticket_number})

            # Strip HTML tags for plain text version
            plain_message = strip_tags(html_message)

            # Create EmailMessage instance
            email_message = EmailMultiAlternatives(
                subject='Les Productions 725 - Vos Billet(s)',
                body=plain_message,  # Plain text message
                from_email=settings.EMAIL_HOST_USER,
                to=[instance.email],
            )

            # Attach ticket image to the email
            for ticket in available_tickets:
                file_path = os.path.join(
                    '../img/', f'ticket_{ticket.ticket_id}.png')
                # Assuming image is stored locally
                email_message.attach_file(file_path)

            # Attach HTML message as an alternative content type
            email_message.attach_alternative(html_message, "text/html")

            # Send email
            email_message.send()

        return Response({'message': 'Order updated successfully'}, status=status.HTTP_200_OK)


class CreateTicketView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create_tickets(self, start, end):
        for i in range(start, end + 1):
            ticket_id = i

            jwt_payload = {
                'ticket_id': ticket_id,
            }
            jwt_token = jwt.encode(jwt_payload, secret, algorithm='HS256')
            print(jwt_token)

            qr_payload = f"https://www.lesproductions725.com/verify/{jwt_token}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_payload)

            img = qr.make_image(fill_color="black", back_color="white")

            ticket_template_path = os.path.join(
                current_directory, '../../ticket_template3.png')

            ticket_template = Image.open(ticket_template_path)
            # position = (743, 612)
            position = (1145, 140)
            # img = img.resize((140, 140))
            img = img.resize((210, 210))
            ticket_template.paste(img, position)

            file_path = os.path.join('../img', f"ticket_{ticket_id}.png")

            ticket_template.save(file_path)
            tickets = Ticket.objects.create(ticket_id=ticket_id)

    def post(self, request):
        start = int(request.GET.get('start', 1))
        end = int(request.GET.get('end', 100))
        self.create_tickets(start, end)
        return Response({'message': 'Tickets created successfully'}, status=status.HTTP_201_CREATED)
