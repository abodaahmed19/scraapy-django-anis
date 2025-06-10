# from django.test import TestCase
# from rest_framework.test import APIClient, APITestCase
# from .models import Bill, InvoiceItem
# from pms.models import User
# from rest_framework.authtoken.models import Token
# from django.utils import timezone
# import datetime
# from django.core.files.uploadedfile import SimpleUploadedFile
# import uuid
# import json
# from knox.models import AuthToken

# BASE_URL = '/api/billing/'

# # Create your tests here.
# class BaseTest(APITestCase):
#     USER_DETAILS = {
#         'email': 'testuser@test.com',
#         'password': 'testpassword',
#         'name': 'test user',
#     }

#     def create_user(self, user_type, email):
#         user_details = self.USER_DETAILS.copy()
#         user_details['email'] = email
#         user_details['user_type'] = user_type
#         user = User.objects.create_user(**user_details)
#         user.is_active = True
#         user.save()
#         return user

#     def create_bill(self, id, user):
#         bill = Bill.objects.create(id=id, title="Ha-SIM-03", category=Bill.PURCHASE_INVOICE, status=Bill.DRAFT, issue_date=timezone.now(),due_date=timezone.now(), uploaded_by=user,  contract_number="09652565352", zatca_qr=None, base64_invoice=None, invoice_hash=None )
#         return bill
    
#     def create_service(self, bill ):
#         item = InvoiceItem.objects.create(bill=bill, description="Description", quantity=22, price=54.00)
#         item.save()
#         return item
    
#     def setBase(self):
#         self.client = APIClient()

#         self.business_user = self.create_user("business", 'test2@test.com')
#         self.individual_user = self.create_user("individual", 'test3@test.com')

#         # create user tokens
#         _, self.business_user_token = AuthToken.objects.create(user=self.business_user)
#         _, self.individual_user_token = AuthToken.objects.create(user=self.individual_user)

#         # create bill
#         self.bill = self.create_bill(uuid.UUID("c0696ced-0537-44bc-9cfe-5735edcdb0bc"), self.business_user,)
#         self.bill1 = self.create_bill(uuid.UUID("c0696ced-0537-44bc-9cfe-5735edcdb34c"), self.individual_user,)

#         # create bill
#         self.service = self.create_service(self.bill)
        

#         # get file
#         self.file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")


# class BillListTest(BaseTest):
    
#     def setUp(self):
#         self.setBase()
#         self.url = f'{BASE_URL}'

#     def test_get_bills(self):
#         response = self.client.get(self.url, HTTP_AUTHORIZATION='Token ' + self.business_user_token)
#         self.assertEqual(response.status_code, 200)


# class BillDetailTest(BaseTest):
#     def setUp(self):
#         self.setBase()
#         self.bill1 = self.create_bill(uuid.UUID("c0696ced-0537-44bc-9cfe-5735edcdb045"), self.business_user,)
#         self.bill2 = self.create_bill(uuid.UUID("c0696ced-0537-44bc-9cfe-5735edcdb023"), self.individual_user,)
#         self.bill3 = self.create_bill(uuid.UUID("c0696ced-0537-74bc-9cfe-5735edcdb023"), self.business_user,)
#         self.url = f'{BASE_URL}{self.bill1.id}/'


#     def test_get_bill(self):
#         response = self.client.get(self.url, HTTP_AUTHORIZATION="Token " + self.business_user_token)
#         self.assertEqual(response.status_code, 200)

#     def test_get_bill_no_bill(self):
#         self.url = BASE_URL + str(self.bill2.id) + "/"
#         response = self.client.get(self.url, HTTP_AUTHORIZATION="Token " + self.business_user_token)
#         self.assertEqual(response.status_code, 404)