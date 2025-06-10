# # signals.py
# from django.core.mail import send_mail
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from .models import User

# @receiver(post_save, sender=User)
# def send_driver_welcome_email(sender, instance, created, **kwargs):
#     if created and instance.is_driver:  # Assuming you have an `is_driver` field
#         subject = "Your Driver Account Has Been Created!"
        
#         # Customize this template or use plain text
#         html_message = render_to_string('email/driver_welcome.html', {
#             'user': instance,
#             'activation_link': instance.get_activation_link()  # Optional: Link to activate
#         })
#         plain_message = strip_tags(html_message)  # Fallback for non-HTML clients

#         send_mail(
#             subject=subject,
#             message=plain_message,
#             from_email="no-reply@yourdomain.com",  # Update this
#             recipient_list=[instance.email],
#             html_message=html_message,
#             fail_silently=False,
#         )
from django.db.models.signals import post_save
from django.dispatch import receiver
from bms.models import OrderTracking
from driver.models import DriverOrderTracking
from django.utils import timezone

@receiver(post_save, sender=DriverOrderTracking)
def sync_driver_tracking_to_order_tracking(sender, instance, **kwargs):
    # جلب OrderTracking المرتبط من خلال TrackingSystemAddress
    tracking = OrderTracking.objects.filter(
        order_item__tracking_system_addresses=instance.tracking_system_address
    ).first()

    if tracking:
        tracking.status = instance.status

        # إضافة end_time إذا وصل السائق لحالة DROP_OFF
        if instance.status == DriverOrderTracking.DROP_OFF and not instance.end_time:
            instance.end_time = timezone.now()
            instance.save()

        tracking.save()