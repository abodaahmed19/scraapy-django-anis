# sms/utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_order_approved_email(order):
    subject = f"Your order #{order.id} has been approved"
    message = (
        f"Hello {order.user.name},\n\n"
        f"Your order #{order.id} has been approved successfully.\n"
        f"Pickup Address: {order.pickup_address}\n"
        f"Total Items: {order.total_items}\n"
        f"Total Amount: {order.total_amount} SAR\n\n"
        f"Thank you for using our recycling service."
    )
    recipient_email = order.user.email

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=False,
    )


