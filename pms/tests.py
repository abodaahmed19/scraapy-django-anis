from rest_framework.test import APITestCase, APIClient
from .models import User, BusinessProfile

from knox.models import AuthToken


class BaseTest(APITestCase):
    def setUp(self):
        self.user_login_data = {
            "email": "test@test.com",
            "password": "testpassword",
        }
        self.user_data = {
            "name": "testUser",
            "user_type": "business",
            "is_active": True,
        }
        self.business_cr = {"cr_number": "1234567890"}
        self.business_data = {
            "address_line1": "test address",
            "address_line2": "test address2",
            "city": "test city",
            "province": "test province",
            "zip_code": "123456",
            "country": "test country",
            "longitude": 23.123,
            "latitude": 23.123,
            "operational_address": "test operational address",
            "primary_contact_person_name": "test name",
            "primary_contact_person_position": "test position",
            "primary_contact_person_contact_number": "+923001234567",
            "primary_contact_person_email_address": "test@test.com",
            "vat_number": "311111111111113",
            "mwan_license_number": "1234567890",
        }
        self.client = APIClient()


class TestUserModel(BaseTest):
    def setUp(self):
        super().setUp()
        register_data = {**self.user_login_data, **self.user_data}
        self.user = User.objects.create_user(**register_data)

    def test_user_email_login_override(self):
        response = self.client.post("/api/users/token/login/", self.user_login_data)
        self.assertEqual(response.status_code, 200)


class TestBusinessProfileModel(BaseTest):
    def setUp(self):
        super().setUp()
        register_data = {**self.user_login_data, **self.user_data}
        self.user = User.objects.create_user(**register_data)
        _, self.user_token = AuthToken.objects.create(user=self.user)

    def test_business_profile_view(self):
        BusinessProfile.objects.create(user=self.user, cr_number="1234567890")
        response = self.client.get(
            "/api/users/business-profile/",
            HTTP_AUTHORIZATION="Token " + self.user_token,
        )
        self.assertEqual(response.status_code, 200)

    def test_business_profile_creation(self):
        response = self.client.post(
            "/api/users/business-profile/",
            self.business_cr,
            HTTP_AUTHORIZATION="Token " + self.user_token,
        )
        self.assertEqual(response.status_code, 201)

    def test_business_profile_patch(self):
        self.client.post(
            "/api/users/business-profile/",
            self.business_cr,
            HTTP_AUTHORIZATION="Token " + self.user_token,
        )
        response = self.client.patch(
            "/api/users/business-profile/",
            self.business_data,
            HTTP_AUTHORIZATION="Token " + self.user_token,
        )
        self.assertEqual(response.status_code, 200)


class TestBusinessApproval(BaseTest):
    def setUp(self):
        super().setUp()
        register_data = {**self.user_login_data, **self.user_data}
        business_user = User.objects.create_user(**register_data)
        self.business_profile = BusinessProfile.objects.create(
            user=business_user, cr_number="1234567890"
        )
        # create admin user
        register_data["email"] = "test2@test.com"
        del register_data["is_active"]
        self.admin_user = User.objects.create_superuser(**register_data)
        _, self.admin_token = AuthToken.objects.create(user=self.admin_user)

    def test_business_list_pending(self):
        response = self.client.get(
            "/api/users/staff/",
            HTTP_AUTHORIZATION="Token " + self.admin_token,
        )
        self.assertEqual(response.status_code, 200)

    def test_business_approval(self):
        self.client.post(
            "/api/users/staff/" + self.business_profile.cr_number + "/approve/",
            HTTP_AUTHORIZATION="Token " + self.admin_token,
        )
        self.business_profile.refresh_from_db()
        self.assertEqual(self.business_profile.status, "approved")

    def test_business_rejection(self):
        self.client.post(
            "/api/users/staff/" + self.business_profile.cr_number + "/reject/",
            HTTP_AUTHORIZATION="Token " + self.admin_token,
        )
        self.business_profile.refresh_from_db()
        self.assertEqual(self.business_profile.status, "rejected")


class TestNotificationModel(BaseTest):
    def setUp(self):
        super().setUp()
        register_data = {**self.user_login_data, **self.user_data}
        self.user = User.objects.create_user(**register_data)
        _, self.user_token = AuthToken.objects.create(user=self.user)

    def test_notification_view(self):
        response = self.client.get(
            "/api/users/notifications/",
            HTTP_AUTHORIZATION="Token " + self.user_token,
        )
        self.assertEqual(response.status_code, 200)
