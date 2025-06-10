from django.db.models.signals import pre_save, post_delete,post_migrate,post_save
from django.dispatch import receiver
from .models import ExtraField, Image,Item,Category,CategoryGroup
from pms.models import User, Notification
import os
@receiver(post_migrate)
def create_default_certificates(sender, **kwargs):
    if sender.name != "inventory":
        return
    return  # <-- temporairement désactivé pour éviter l'exécution du code suivant
    from .models import CertificateType  
    default_certificates = [
        {"name": "Aramco Certificate", "description": "Certificate for Aramco compliance."},
        {"name": "Maaden Certificate", "description": "Certificate for Maaden compliance."},
        {"name": "SCECO Certificate", "description": "Certificate for SCECO compliance."},
        {"name": "ISO Certificate", "description": "ISO certification for quality standards."},
        {"name": "SABIC Certification", "description": "SABIC safety and compliance certificate."},
        {"name": "Mwan Certificate", "description": "MWAN industry compliance certificate."},
        {"name": "OSHA Certificate", "description": "Occupational Safety and Health Administration certification."},
        {"name": "equipmentLicense", "description": "equipmentLicense certification."},
        {"name": "driverId", "description": "driverId certification."},
        {"name": "driversLicense", "description": "driversLicense certification."},
    ]
    for cert in default_certificates:
        CertificateType.objects.get_or_create(name=cert["name"], defaults={"description": cert["description"]})
            
            
@receiver(pre_save, sender=Image)
def check_thumbnail_and_image(sender, instance, **kwargs):
    if instance.is_thumbnail:
        Image.objects.filter(item=instance.item).update(is_thumbnail=False)
    # delete image if its changed
    if instance.pk:
        old_image = Image.objects.get(pk=instance.pk)
        if old_image.image != instance.image:
            if os.path.isfile(old_image.image.path):
                os.remove(old_image.image.path)
@receiver(post_delete, sender=Image)
def delete_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
    # set another image as thumbnail if deleted image was thumbnail
    if instance.is_thumbnail:
        images = Image.objects.filter(item=instance.item)
        if images.exists():
            image = images.first()
            image.is_thumbnail = True
            image.save()
@receiver(pre_save, sender=Item)
def track_item_changes(sender, instance, **kwargs):
    if instance.pk:  # Only for existing items
        try:
            instance._old_status = Item.objects.get(pk=instance.pk).status
        except Item.DoesNotExist:
            pass
    
@receiver(pre_save, sender=Item)
def update_last_max_quantity(sender, instance, **kwargs):
    if not instance.pk:
        instance.last_max_quantity = instance.quantity
    else:
        original = sender.objects.get(pk=instance.pk)
        if  original.quantity is None or instance.quantity > original.quantity:
            instance.last_max_quantity = instance.quantity
            
@receiver(post_save, sender=Item)
def handle_item_notifications(sender, instance, created, **kwargs):
    if created:
        print('created new item', instance.name)
        staff = User.objects.filter(is_staff=True)
        for user in staff:
            Notification.objects.create(
                user=user,
                title=f'{instance.name} requires approval',
                description=f"{instance.name} added to {instance.owner.name}'s inventory"
            )
    else:
        
        old_status = getattr(instance, '_old_status', None)
        if old_status != instance.status:
            print('changed item', instance.name, 'from', instance._old_status, 'to', instance.status)
            Notification.objects.create(
                user=instance.owner,
                title=f'{instance.name} status updated',
                description=f'Changed from {old_status} to {instance.status}'
            )
    if not instance.category.category_group.group_type == CategoryGroup.RENTAL:
        if instance.category.category_group.group_type == CategoryGroup.SERVICE:
            instance.quantity = 1
            instance.last_mAx_quantity = 1
        if instance.last_max_quantity is not None and  instance.quantity < (instance.last_max_quantity/10):
            Notification.objects.create(
                user=instance.owner,
                title=f'{instance.name} is running out of stock',
                description=f'{instance.name} is running out of stock with less than 10% in stock'
            )
@receiver(post_save, sender=Category)
def category_send_notifiaction(sender, instance,created, **kwargs):
    if created:
        staff = User.objects.filter(is_staff=True)
        for user in staff:
            Notification.objects.create(
                user=user,
                title=f'{instance.name} requires approval',
                description=f"{instance.name} has been requested"
            )
    else:
    
        if hasattr(instance, 'author') and instance.author:
            Notification.objects.create(
                user=instance.author,
                title=f'{instance.name} requested category has been {instance.status}',
                description=f'{instance.name} requested category has been {instance.status}'
            )