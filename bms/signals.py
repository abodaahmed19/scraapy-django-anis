from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import OrderItem, OrderTracking, OrderItemReport,TrackingSystemAddresses
from dms.models import UserDocuments
from pms.models import User, Notification,Address
from inventory.models import CategoryGroup
from django.db.models.signals import post_save,post_delete
import os


@receiver(post_save, sender=OrderItem)
def create_order_tracking(sender, instance, created, **kwargs):
    if created:  
        OrderTracking.objects.create(order_item=instance)

@receiver(pre_save, sender=OrderItem)
def create_tracking_system_addresses(sender, instance, **kwargs):
    if not instance.pk:

        item_address = Address.objects.create(
            name = 'item_address',
            address_line1 = instance.item.address_line1 ,
            address_line2 = instance.item.address_line2 ,
            city = instance.item.city ,
            province = instance.item.province ,
            zip_code = instance.item.zip_code ,
            country = instance.item.country ,
            longitude = instance.item.longitude,
            latitude = instance.item.latitude ,
            on_site_contact_name = instance.item.on_site_contact_name ,
            on_site_contact_phone = instance.item.on_site_contact_phone
        )

        print('shipping option',instance.order.shipping_option)
        if instance.order.shipping_option == 1:
            print('in the if of tracking system')
            user_address = Address.objects.create(
            name = instance.order.addressName,
            address_line1 = instance.order.delivery_address_line1 ,
            address_line2 = instance.order.delivery_address_line2 ,
            city = instance.order.delivery_city ,
            province = instance.order.delivery_province ,
            zip_code = instance.order.delivery_zip_code ,
            country = instance.order.delivery_country ,
            longitude = instance.order.longitude ,
            latitude = instance.order.latitude ,
            on_site_contact_name = instance.order.delivery_contact_name ,
            on_site_contact_phone = instance.order.delivery_contact_phone)
            track = TrackingSystemAddresses.objects.create(
                    pickup_address = item_address,
                    destination_address = user_address,
                )
        else:
            print('in the else of tracking system')
            track = TrackingSystemAddresses.objects.create(
                destination_address = item_address,
            )

        instance.tracking_system_addresses = track        

@receiver(post_save, sender=OrderItem)
def create_document_meta(sender,instance,created,**kwargs):
    if created and instance.category.require_contract:
        UserDocuments.objects.create(order_item=instance,type=UserDocuments.MARKDOWN,user=instance.order.buyer)
    if created and instance.category.send_certificate:
        UserDocuments.objects.create(order_item=instance,type=UserDocuments.JSON,user=instance.order.buyer)


@receiver(post_save, sender=OrderItemReport)
def create_document_meta_for_item_document(sender,instance,created,**kwargs):
    print("error here")
    if created:
        UserDocuments.objects.create(order_item_report=instance,order_item=instance.order_item,type=UserDocuments.FILE,user=instance.order_item.order.buyer)

@receiver(pre_save, sender=OrderTracking)
def check_status_update(sender, instance, **kwargs):
    if instance.pk:
        previous_status = OrderTracking.objects.get(pk=instance.pk).status
        if instance.status != previous_status:  
            category_group_type = instance.order_item.category.category_group.group_type

            if instance.status != OrderTracking.REVIEWING:
                if category_group_type == CategoryGroup.PRODUCT and instance.status not in dict(OrderTracking.PRODUCT_STATUS):
                    raise ValueError(f"Invalid status '{instance.status}' for product category")
                elif category_group_type == CategoryGroup.RENTAL and not dict(OrderTracking.RENTAL_STATUS).get(previous_status):
                    raise ValueError("Invalid status for rental category")
                elif category_group_type == CategoryGroup.SERVICE and not dict(OrderTracking.SERVICE_STATUS).get(previous_status):
                    raise ValueError("Invalid status for service category")
                
                #If the status is changed to 'RECEIVED', set the status to 'COMPLETE'
                if instance.status == OrderTracking.DROP_OFF:
                    instance.status = OrderTracking.COMPLETE
                # same but for pickup
                if instance.status == OrderTracking.RECEIVED:
                    instance.status = OrderTracking.COMPLETE

                print("the new status2",instance.status)
                if instance.status == OrderTracking.READY and instance.order_item.order.shipping_option == 1:
                    drivers = instance.order_item.owner.drivers.all()
                    for driver in drivers:
                        notification = Notification.objects.create(
                            user=driver.user,
                            title=f'{instance.order_item.name} is ready for shipment',
                            description=f"{instance.order_item.name} is ready for shipment"
                        )
                        print('the notification',notification)
                    
    else:
        if (
            instance.order_item.owner.business_profile.product_auto_accept
            and instance.order_item.category.category_group.group_type == CategoryGroup.PRODUCT
        ):
            instance.status = OrderTracking.PREPARING
        elif (
            instance.order_item.owner.business_profile.rental_auto_accept
            and instance.order_item.category.category_group.group_type == CategoryGroup.RENTAL
        ):
            instance.status = OrderTracking.ACCEPTED
        elif (
            instance.order_item.owner.business_profile.service_auto_accept
            and instance.order_item.category.category_group.group_type == CategoryGroup.SERVICE
        ):
            instance.status = OrderTracking.OBTAINED
        else:
            instance.status = OrderTracking.REVIEWING


# @receiver(pre_save, sender=OrderTracking)
# def check_status_update(sender, instance, **kwargs):
#     if instance.pk:

#         previous_status = OrderTracking.objects.get(pk=instance.pk).status
#         print('prev',previous_status)
#         print ('current',instance.status)
#         if instance.status != previous_status:  
#             category_group_type = instance.order_item.category.category_group.group_type

#             if (instance.status != OrderTracking.REVIEWING):
#             # Validate the status based on the category group type
#                 print('testing this',dict(OrderTracking.PRODUCT_STATUS).get(previous_status))

#                 if category_group_type == CategoryGroup.PRODUCT and not dict(OrderTracking.PRODUCT_STATUS).get(previous_status):
#                     raise ValueError("Invalid status for product category")
                
#                 elif category_group_type == CategoryGroup.RENTAL and not dict(
#                     OrderTracking.RENTAL_STATUS
#                 ).get(instance.status):
                    
#                     raise ValueError("Invalid status for rental category")
#                 elif category_group_type == CategoryGroup.SERVICE and not dict( OrderTracking.SERVICE_STATUS).get(previous_status):
#                     raise ValueError("Invalid status for service category")
                
#     else:
#         print("in the else of signaling")
#         if (
#             instance.order_item.owner.business_profile.product_auto_accept
#             and instance.order_item.category.category_group.group_type == CategoryGroup.PRODUCT
#         ):
#             instance.status = OrderTracking.PREPARING
#         elif (
#             instance.order_item.owner.business_profile.rental_auto_accept
#             and instance.order_item.category.category_group.group_type == CategoryGroup.RENTAL
#         ):
#             instance.status = OrderTracking.ACCEPTED
#         elif (
#             instance.order_item.owner.business_profile.service_auto_accept
#             and instance.order_item.category.category_group.group_type == CategoryGroup.SERVICE
#         ):
#             instance.status = OrderTracking.OBTAINED
#         else:
#             instance.status = OrderTracking.REVIEWING

@receiver(post_save, sender=OrderTracking)
def tracking_send_notification(sender, instance, created, **kwargs):
    Notification.objects.create(
        user=instance.order_item.order.buyer,
        title=f"{instance.order_item.name} status updated",
        description=f"Status changed to {instance.status}")


@receiver(post_delete, sender=OrderItemReport)
def delete_order_item_report_file(sender, instance, **kwargs):

    if instance.report:
        if os.path.isfile(instance.report.path):
            os.remove(instance.report.path)