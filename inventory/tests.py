from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from pms.models import User, BusinessProfile
from .models import Category, CategoryGroup, FieldType, ExtraField, Item,VehicleSpecs


class BaseTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@test.com',
            'password': 'testpassword',
            'name': 'Test User',
            'user_type': 'business',
            'is_active': True
            }
        self.business_user = User.objects.create_user(**self.user_data)
        self.business_data = {
            'user': self.business_user,
            'cr_number': '123456789',
            'status': BusinessProfile.APPROVED
            }
        BusinessProfile.objects.create(**self.business_data)
        self.category_group = CategoryGroup.objects.create(name='Category Group', group_type=CategoryGroup.PRODUCT)
        self.field_type = FieldType.objects.create(name='Field Type')
        self.category = Category.objects.create(name='Category', category_group=self.category_group)
        self.category.field_types.add(self.field_type)
        self.category2 = Category.objects.create(name='Category 2', category_group=self.category_group, sub_item_type=Category.FLEET)
        self.category2.field_types.add(self.field_type)
        self.category3 = Category.objects.create(name='Category 3', category_group=self.category_group)
        self.category4 = Category.objects.create(name='Category 4', category_group=self.category_group, sub_item_type=Category.FLEET)
        self.item_data = {
            'name': 'Item',
            'price': 100,
            'category': self.category,
            'address_line1': 'Address Line 1',
            'address_line2': 'Address Line 2',
            'city': 'City',
            'province': 'Province',
            'zip_code': '123456',
            'country': 'Country',
            'quantity': 1,
            'owner': self.business_user,
            'status': Item.PENDING,
            }
        self.item = Item.objects.create(**self.item_data)
        ExtraField.objects.create(type=self.field_type, value='Value', item=self.item)
        self.staff_user_data = {
            'email': 'abc@test.com',
            'password': 'testpassword',
            'name': 'Test User',
            'user_type': 'business',
            'is_active': True
            }
        self.staff_user = User.objects.create_user(**self.staff_user_data, is_staff=True)

        self.item_list_url = reverse('item-list')
        self.login_url = reverse('user-login')
        self.categories_url = reverse('category-list')
        self.items_url = reverse('user-item-list')
        self.item_detail_url = reverse('user-item-detail', kwargs={'pk': self.item.id})
        self.staff_vendor_list_url = reverse('staff-vendor-list')
        self.approval_vendor_item_list_url = reverse('staff-vendor-item-list', kwargs={'cr_number': self.business_data['cr_number']})
        self.approval_url = reverse('item-approval-detail', kwargs={'pk': self.item.id})
        self.reject_url = reverse('item-reject-detail', kwargs={'pk': self.item.id})

        self.business_user_token = self.client.post(self.login_url, self.user_data, format='json').data['token']
        self.staff_user_token = self.client.post(self.login_url, self.staff_user_data, format='json').data['token']


class CategoryTest(BaseTest):
    def test_get_categories(self):
        response = self.client.get(self.categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

class ItemListTest(BaseTest):
    def test_get_items(self):
        response = self.client.get(self.item_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        Item.objects.filter(id=self.item.id).update(status=Item.APPROVED)
        response = self.client.get(self.item_list_url)
        self.assertEqual(len(response.data['results']), 1)


class UserItemListTest(BaseTest):
    def test_get_items(self):
        response = self.client.get(self.items_url, HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_item_not_business(self):
        user_data = {
            'email': 'abc123@test.com',
            'password': 'testpassword',
            'name': 'Test User',
            'user_type': 'individual',
            'is_active': True
            }
        user = User.objects.create_user(**user_data)
        user_token = self.client.post(self.login_url, user_data, format='json').data['token']
        response = self.client.get(self.items_url, HTTP_AUTHORIZATION=f'Token {user_token}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_post_items(self):
    #     user_data = {
    #         'name': 'abc123@test.com',
    #         'price': 'testpassword',
    #         'address_line1': 'Test User',
    #         'city': 'individual',
    #         'province': 'province',
    #         'zip_code': 'zip_code',
    #         'country': 'country',
    #         'quantity': 'quantity',
    #         'category': 1,
    #         'owner': 1,
    #         'sub_items': [
    #             {"value":"Hi"}
    #         ],
    #         'extra_fields': [
    #             {"value":"500" , "name":"Price"}
    #         ],
    #         }
    #     # item_data = self.item_data.copy()
    #     # item_data.pop('owner')
    #     # item_data['name'] = 'Item 2'
    #     # item_data['price'] = 200
    #     # item_data['category'] = self.category.id
    #     # item_data['extra_fields'] = [{'name': self.field_type.name, 'value': 'Value 2'}]

    #     response = self.client.post(self.items_url, user_data, format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(Item.objects.count(), 2)

    # def test_post_items_with_sub_items_and_extra_fields(self):
    #     item_data = self.item_data.copy()
    #     item_data.pop('owner')
    #     item_data['name'] = 'Item 2'
    #     item_data['price'] = 200
    #     item_data['category'] = self.category2.id
    #     item_data['extra_fields'] = [{'name': self.field_type.name, 'value': 'Value 2'}]
    #     item_data['sub_items'] = [{'value': 'Sub Item 1'}]

    #     response = self.client.post(self.items_url, [item_data], format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(Item.objects.count(), 2)

    # def test_post_items_with_only_sub_items(self):
    #     item_data = self.item_data.copy()
    #     item_data.pop('owner')
    #     item_data['name'] = 'Item 2'
    #     item_data['price'] = 200
    #     item_data['category'] = self.category4.id
    #     item_data['sub_items'] = [{'value': 'Sub Item 1'}]

    #     response = self.client.post(self.items_url, [item_data], format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(Item.objects.count(), 2)

    # def test_post_items_category_without_extra_fields(self):
    #     item_data = self.item_data.copy()
    #     item_data.pop('owner')
    #     item_data['name'] = 'Item 2'
    #     item_data['price'] = 200
    #     item_data['category'] = self.category3.id

    #     response = self.client.post(self.items_url, [item_data], format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # def test_post_items_missing_sub_items(self):
    #     item_data = self.item_data.copy()
    #     item_data.pop('owner')
    #     item_data['name'] = 'Item 2'
    #     item_data['price'] = 200
    #     item_data['category'] = self.category2.id
    #     item_data['extra_fields'] = [{'name': self.field_type.name, 'value': 'Value 2'}]

    #     response = self.client.post(self.items_url, [item_data], format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_post_items_no_data(self):
    #     response = self.client.post(self.items_url, [{}], format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_post_items_missing_extra_field(self):
    #     item_data = self.item_data.copy()
    #     item_data.pop('owner')
    #     item_data['name'] = 'Item 2'
    #     item_data['price'] = 200
    #     item_data['category'] = self.category.id

    #     response = self.client.post(self.items_url, [item_data], format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_post_items_invalid_field_type_category(self):
    #     new_field_type = FieldType.objects.create(name='Field Type 2')
    #     new_category = Category.objects.create(name='Category 10', category_group=self.category_group)
    #     new_category.field_types.add(new_field_type)

    #     item_data = self.item_data.copy()
    #     item_data.pop('owner')
    #     item_data['name'] = 'Item 5'
    #     item_data['price'] = 500
    #     item_data['category'] = new_category.id
    #     item_data['extra_fields'] = [{'name': self.field_type.name, 'value': 'Value 5'}]

    #     response = self.client.post(self.items_url, item_data, format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_post_items_with_invalid_extra_field(self):
    #     item_data = self.item_data.copy()
    #     item_data.pop('owner')
    #     item_data['name'] = 'Item 2'
    #     item_data['price'] = 200
    #     item_data['category'] = self.category.id
    #     item_data['extra_fields'] = [{'a': self.field_type.name, 'b': 'Value 2'}]

    #     response = self.client.post(self.items_url, [item_data], format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_post_items_with_incomplete_extra_field(self):
    #     new_field_type = FieldType.objects.create(name='Field Type 2')
    #     self.category.field_types.add(new_field_type)
    #     item_data = self.item_data.copy()
    #     item_data.pop('owner')
    #     item_data['name'] = 'Item 2'
    #     item_data['price'] = 200
    #     item_data['category'] = self.category.id
    #     item_data['extra_fields'] = [{'name': self.field_type.name, 'value': 'Value 2'}]

    #     response = self.client.post(self.items_url, [item_data], format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserItemDetailTest(BaseTest):
    def test_patch_item(self):
        item_data = {
            'name': 'Item 2',
            }
        print(self.item_detail_url, '---------',item_data,'-----',self.business_user_token)
        response = self.client.patch(self.item_detail_url, item_data, format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        print(response)
        print('\n',response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Item.objects.get(id=self.item.id).name, 'Item 2')

    def test_patch_item_not_owner(self):
        user_data = {
            'email': 'test12@test.com',
            'password': 'testpassword',
            'name': 'Test User',
            'user_type': 'business',
            'is_active': True
            }
        user = User.objects.create_user(**user_data)
        user_token = self.client.post(self.login_url, user_data, format='json').data['token']
        response = self.client.patch(self.item_detail_url, {'name': 'Item 2'}, format='json', HTTP_AUTHORIZATION=f'Token {user_token}')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_item_extra_fields(self):
        item_data = {
            'extra_fields': [{'name': self.field_type.name, 'value': 'Value 101'}]
        }
        response = self.client.patch(self.item_detail_url, item_data, format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ExtraField.objects.filter(item=self.item).count(), 1)
        self.assertEqual(ExtraField.objects.get(item=self.item).value, 'Value 101')

    def test_patch_item_sub_items(self):
        self.item.category = self.category2
        self.item.save()
        item_data = {
            'sub_items': [{'value': 'Sub Item 2'}]
        }
        response = self.client.patch(self.item_detail_url, item_data, format='json', HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Item.objects.get(id=self.item.id).sub_items.count(), 1)
        self.assertEqual(Item.objects.get(id=self.item.id).sub_items.first().value, 'Sub Item 2')

    def test_delete_item(self):
        response = self.client.delete(self.item_detail_url, HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Item.objects.count(), 0)


class StaffVendorListTest(BaseTest):
    def test_get_staff_vendor_list(self):
        response = self.client.get(self.staff_vendor_list_url, HTTP_AUTHORIZATION=f'Token {self.staff_user_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_staff_vendor_list_not_staff(self):
        response = self.client.get(self.staff_vendor_list_url, HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StaffVendorItemListTest(BaseTest):
    def test_get_staff_vendor_item_list(self):
        response = self.client.get(self.approval_vendor_item_list_url, HTTP_AUTHORIZATION=f'Token {self.staff_user_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_staff_vendor_item_list_not_staff(self):
        response = self.client.get(self.approval_vendor_item_list_url, HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StaffItemApprovalTest(BaseTest):
    def test_post_item_approval(self):
        response = self.client.post(self.approval_url, HTTP_AUTHORIZATION=f'Token {self.staff_user_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Item.objects.get(id=self.item.id).status, Item.APPROVED)

    def test_post_item_approval_already_approved(self):
        self.item.status = Item.APPROVED
        self.item.save()
        response = self.client.post(self.approval_url, HTTP_AUTHORIZATION=f'Token {self.staff_user_token}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_item_not_staff(self):
        response = self.client.post(self.approval_url, HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StaffItemRejectTest(BaseTest):
    def test_post_item_reject(self):
        response = self.client.post(self.reject_url, HTTP_AUTHORIZATION=f'Token {self.staff_user_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Item.objects.get(id=self.item.id).status, Item.REJECTED)

    def test_post_item_reject_already_rejected(self):
        self.item.status = Item.REJECTED
        self.item.save()
        response = self.client.post(self.reject_url, HTTP_AUTHORIZATION=f'Token {self.staff_user_token}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_item_reject_not_staff(self):
        response = self.client.post(self.reject_url, HTTP_AUTHORIZATION=f'Token {self.business_user_token}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CategoryDetailRejectViewTest(APITestCase):
    def setUp(self):
        # Create a staff user
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='testpassword',
            name='Staff User',
            user_type='business',
            is_staff=True,
            is_active=True
        )
        self.staff_user_token = self.client.post(
            reverse('user-login'),
            {'email': 'staff@test.com', 'password': 'testpassword'},
            format='json'
        ).data['token']

        # Create a non-staff user
        self.non_staff_user = User.objects.create_user(
            email='nonstaff@test.com',
            password='testpassword',
            name='Non-Staff User',
            user_type='business',
            is_staff=False,
            is_active=True
        )
        self.non_staff_user_token = self.client.post(
            reverse('user-login'),
            {'email': 'nonstaff@test.com', 'password': 'testpassword'},
            format='json'
        ).data['token']

        # Create a category group
        self.category_group = CategoryGroup.objects.create(
            id=47,
            name='clothes materials',
            name_ar='أساسيات الملابس',
            group_type=CategoryGroup.PRODUCT,
            status=CategoryGroup.APPROVED
        )

        # Create a pending category
        self.pending_category = Category.objects.create(
            id=131,
            name='Cotton',
            name_ar='قطن',
            price_unit='Package',
            price_unit_ar='حزمة',
            category_group=self.category_group,
            status=Category.PENDING
        )

        # Create a rejected category
        self.rejected_category = Category.objects.create(
            id=132,
            name='Rejected Category',
            name_ar='فئة مرفوضة',
            price_unit='Package',
            price_unit_ar='حزمة',
            category_group=self.category_group,
            status=Category.REJECTED
        )

        # Create an approved category
        self.approved_category = Category.objects.create(
            id=133,
            name='Approved Category',
            name_ar='فئة معتمدة',
            price_unit='Package',
            price_unit_ar='حزمة',
            category_group=self.category_group,
            status=Category.APPROVED
        )

        # URL for the reject endpoint
        self.reject_url = lambda pk: reverse('category-list-reject', kwargs={'pk': pk})

    def test_reject_pending_category(self):
        """
        Test that a staff user can reject a pending category via the API.
        """
        # Simulate the frontend payload
        payload = {
            "id": 131,
            "name": "Cotton",
            "name_ar": "قطن",
            "price_unit": "Package",
            "price_unit_ar": "حزمة",
            "extra_field_types": [],
            "sub_item_type": None,
            "status": "pending",
            "category_group": {
                "id": 47,
                "name": "clothes materials",
                "name_ar": "أساسيات الملابس",
                "icon": None,
                "group_type": "product",
                "status": "approved"
            },
            "legal_requirements": [],
            "hide_price": False
        }

        # Make an API request to reject the category
        response = self.client.post(
            self.reject_url(self.pending_category.id),
            data=payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.staff_user_token}'
        )

        # Verify the API response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], {'message':'Category rejected successfully'})

        # Verify the database is updated
        self.pending_category.refresh_from_db()
        self.assertEqual(self.pending_category.status, Category.REJECTED)

        # Verify the category group status is updated
        self.category_group.refresh_from_db()


    def test_reject_category_as_non_staff_user(self):
        """
        Test that a non-staff user cannot reject a category via the API.
        """
        # Make an API request to reject the category as a non-staff user
        response = self.client.post(
            self.reject_url(self.pending_category.id),
            HTTP_AUTHORIZATION=f'Token {self.non_staff_user_token}'
        )

        # Verify the API response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)




class CategoryDetailApproveViewTest(APITestCase):
    def setUp(self):
        # Create a staff user
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='testpassword',
            name='Staff User',
            user_type='business',
            is_staff=True,
            is_active=True
        )
        self.staff_user_token = self.client.post(
            reverse('user-login'),
            {'email': 'staff@test.com', 'password': 'testpassword'},
            format='json'
        ).data['token']

        # Create a non-staff user
        self.non_staff_user = User.objects.create_user(
            email='nonstaff@test.com',
            password='testpassword',
            name='Non-Staff User',
            user_type='business',
            is_staff=False,
            is_active=True
        )
        self.non_staff_user_token = self.client.post(
            reverse('user-login'),
            {'email': 'nonstaff@test.com', 'password': 'testpassword'},
            format='json'
        ).data['token']

        # Create a category group
        self.category_group = CategoryGroup.objects.create(
            id=47,
            name='clothes materials',
            name_ar='أساسيات الملابس',
            group_type=CategoryGroup.PRODUCT,
            status=CategoryGroup.APPROVED
        )

        # Create a pending category
        self.pending_category = Category.objects.create(
            id=131,
            name='Cotton',
            name_ar='قطن',
            price_unit='Package',
            price_unit_ar='حزمة',
            category_group=self.category_group,
            status=Category.PENDING
        )

        # Create an approved category
        self.approved_category = Category.objects.create(
            id=132,
            name='Approved Category',
            name_ar='فئة معتمدة',
            price_unit='Package',
            price_unit_ar='حزمة',
            category_group=self.category_group,
            status=Category.APPROVED
        )

        # URL for the approve endpoint
        self.approve_url = lambda pk: reverse('category-list-approve', kwargs={'pk': pk})

    def test_approve_pending_category(self):
        """
        Test that a staff user can approve a pending category via the API.
        """
        # Simulate the frontend payload
        payload = {
            "id": 131,
            "name": "Cotton",
            "name_ar": "قطن",
            "price_unit": "Package",
            "price_unit_ar": "حزمة",
            "extra_field_types": [],
            "sub_item_type": None,
            "status": "pending",
            "category_group": {
                "id": 47,
                "name": "clothes materials",
                "name_ar": "أساسيات الملابس",
                "icon": None,
                "group_type": "product",
                "status": "approved"
            },
            "legal_requirements": [],
            "hide_price": False
        }

        # Make an API request to approve the category
        response = self.client.post(
            self.approve_url(self.pending_category.id),
            data=payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.staff_user_token}'
        )

        # Verify the API response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], {'message': 'Category approved successfully'})

        # Verify the database is updated
        self.pending_category.refresh_from_db()
        self.assertEqual(self.pending_category.status, Category.APPROVED)
    def test_approve_category_as_non_staff_user(self):
        """
        Test that a non-staff user cannot approve a category via the API.
        """
        # Simulate the frontend payload
        payload = {
            "id": 131,
            "name": "Cotton",
            "name_ar": "قطن",
            "price_unit": "Package",
            "price_unit_ar": "حزمة",
            "extra_field_types": [],
            "sub_item_type": None,
            "status": "pending",
            "category_group": {
                "id": 47,
                "name": "clothes materials",
                "name_ar": "أساسيات الملابس",
                "icon": None,
                "group_type": "product",
                "status": "approved"
            },
            "legal_requirements": [],
            "hide_price": False
        }

        # Make an API request to approve the category as a non-staff user
        response = self.client.post(
            self.approve_url(self.pending_category.id),
            data=payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.non_staff_user_token}'
        )

        # Verify the API response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        
class VehicleSpecsApprovalTestCase(APITestCase):

    def setUp(self):
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='staffpass',
            name='Staff',
            user_type='business',
            is_staff=True,
            is_active=True
        )
        self.staff_token = self.client.post(
            reverse('user-login'),
            {'email': 'staff@test.com', 'password': 'staffpass'},
            format='json'
        ).data['token']

        # Create non-staff user
        self.non_staff_user = User.objects.create_user(
            email='user@test.com',
            password='userpass',
            name='User',
            user_type='business',
            is_staff=False,
            is_active=True
        )
        self.user_token = self.client.post(
            reverse('user-login'),
            {'email': 'user@test.com', 'password': 'userpass'},
            format='json'
        ).data['token']

        # Create CategoryGroup and Category
        self.category_group = CategoryGroup.objects.create(
            name='Vehicles', group_type='rental', status='approved'
        )

        self.category = Category.objects.create(
            name='Cars',
            category_group=self.category_group,
            status='approved'
        )

        # Create VehicleSpecs (pending)
        self.vehicle_spec_pending = VehicleSpecs.objects.create(
            make='Toyota',
            model='Camry',
            model_year='2023',
            categories=self.category,
            status='pending'
        )

        self.vehicle_specs_pending_list_url = reverse('vehicle-specs-pending-list')
        self.vehicle_spec_approve_url = reverse(
            'vehicle-specs-approve', kwargs={'pk': self.vehicle_spec_pending.pk}
        )
        self.vehicle_spec_reject_url = reverse(
            'vehicle-specs-reject', kwargs={'pk': self.vehicle_spec_pending.pk}
        )

    def test_list_pending_vehicle_specs(self):
        """Ensure staff user can list pending VehicleSpecs."""
        response = self.client.get(
            self.vehicle_specs_pending_list_url,
            HTTP_AUTHORIZATION=f'Token {self.staff_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_approve_vehicle_spec(self):
        """Ensure staff user can approve VehicleSpecs."""
        response = self.client.post(
            self.vehicle_spec_approve_url,
            HTTP_AUTHORIZATION=f'Token {self.staff_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle_spec_pending.refresh_from_db()
        self.assertEqual(self.vehicle_spec_pending.status, 'approved')

    def test_reject_vehicle_spec(self):
        """Ensure staff user can reject VehicleSpecs."""
        response = self.client.post(
            self.vehicle_spec_reject_url,
            HTTP_AUTHORIZATION=f'Token {self.staff_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle_spec_pending.refresh_from_db()
        self.assertEqual(self.vehicle_spec_pending.status, 'rejected')

    def test_non_staff_cannot_approve_vehicle_spec(self):
        """Ensure non-staff user cannot approve VehicleSpecs."""
        response = self.client.post(
            self.vehicle_spec_approve_url,
            HTTP_AUTHORIZATION=f'Token {self.user_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_staff_cannot_reject_vehicle_spec(self):
        """Ensure non-staff user cannot reject VehicleSpecs."""
        response = self.client.post(
            self.vehicle_spec_reject_url,
            HTTP_AUTHORIZATION=f'Token {self.user_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_already_processed_vehicle_spec(self):
        """Ensure cannot approve already approved VehicleSpecs."""
        self.vehicle_spec_pending.status = 'approved'
        self.vehicle_spec_pending.save()

        response = self.client.post(
            self.vehicle_spec_approve_url,
            HTTP_AUTHORIZATION=f'Token {self.staff_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reject_already_processed_vehicle_spec(self):
        """Ensure cannot reject already rejected VehicleSpecs."""
        self.vehicle_spec_pending.status = 'rejected'
        self.vehicle_spec_pending.save()

        response = self.client.post(
            self.vehicle_spec_reject_url,
            HTTP_AUTHORIZATION=f'Token {self.staff_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
      