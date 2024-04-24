# ticketing/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('validate-ticket/', views.ValidateTicket.as_view(), name='validate_ticket'),
    path('order/', views.CreateOrderAPIView.as_view(), name='order'),
    path('order-list/', views.OrderListAPIView.as_view(), name='order_list'),
    path('update-order/<int:pk>/',
         views.UpdateOrderAPIView.as_view(), name='update_order'),
    path('create-ticket/', views.CreateTicketView.as_view(), name='create_ticket'),
    # path('invalidate-ticket/', views.InvalidateTicket.as_view(),
    #      name='invalidate_ticket'),
]
