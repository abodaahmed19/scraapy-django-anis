# from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import BusinessProfile, Notification ,User
# import os
from django.db.models.signals import post_save,pre_save


# @receiver(pre_save, sender=BusinessProfile)
# def check_business_profile_image(sender, instance, **kwargs):
#     if instance.pk:
#         old_instance = BusinessProfile.objects.get(pk=instance.pk)
#         if old_instance.image and instance.image:
#             if old_instance.image != instance.image:
#                 if os.path.isfile(old_instance.image.path):
#                     os.remove(old_instance.image.path)


# @receiver(post_delete, sender=BusinessProfile)
# def delete_business_profile_image(sender, instance, **kwargs):
#     if instance.image:
#         if os.path.isfile(instance.image.path):
#             os.remove(instance.image.path)

@receiver(post_save, sender=BusinessProfile)
def create_business_profile(sender, instance, created, **kwargs):
    if created:
        staff= User.objects.filter(is_staff=True)
        for user in staff:
            Notification.objects.create(user=user, title=f'{instance.user.name} requiers approval for business profile',description=f'{instance.user.name} requiers approval for business profile')
    # else:
    #     # send message to the business owner of the new status of the business profile
    #     Notification.objects.create(user=instance.user, title=f'{instance.user.username} your business profile has been {instance.status}',description=f'{instance.user.username} your business profile has been {instance.status}')

@receiver(pre_save, sender=BusinessProfile)
def status_change(sender, instance, **kwargs):
    if instance.pk:
        old_instance = BusinessProfile.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            Notification.objects.create(user=instance.user, title=f'{instance.user.name} your business profile has been {instance.status}',description=f'{instance.user.name} your business profile has been {instance.status}')
