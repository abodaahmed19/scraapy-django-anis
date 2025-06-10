# Scraapy project API

## Installation
### Requirements
- docker
- [Start Tool](https://gitlab.hq.uzdsolutions.com/uzdsolutions/start-tool) (optional) see below

### Steps with start tool
1. Clone the repository
2. Install [Start Tool](https://gitlab.hq.uzdsolutions.com/uzdsolutions/start-tool)
3. run app with command
```bash
start
```
or
```bash
start dev
```

### Token authentication
some endpoints require an authentication token, the token can be obtained from the /api/profile/user/login, /api/profile/user/register, /api/profile/business/login/, and /api/profile/business/register/ endpoints
token must be sent in the header as the key "Authorization" and value "Token token_key"
## PMS API endpoints
### /api/profile/user/register/ [POST]
#### Request
```json
{
    "name": "name",
    "email": "email",
    "password": "password",
    "password_confirm": "password_confirm",
    "otp": "otp" // conditional
}
```
#### Response
```json
{
    "message": "message"
}
```
### /api/profile/business/register/ [POST]
#### Request
```json
{
    "name": "name",
    "email": "email",
    "password": "password",
    "otp": "otp" // conditional
}
```
#### Response
```json
{
    "message": "message"
}
```
### /api/profile/login/ [POST]
#### Request
```json
{
    "email": "email",
    "password": "password", // optional
    "otp": "otp" // conditional
}
```
#### Response
```json
{
    "token": "token",
    "redirect_url": "redirect_url"
}
```
### /api/profile/logout/ [POST] (authentication required)
### /api/profile/forgot-password/ [POST] 
#### Request
```json
{
    "email": "email",
    "otp": "otp", // conditional
    "forgot_token": "forgot_token", // conditional
    "password": "password", // conditional
    "password_confirm": "password_confirm" // conditional
}
```
#### Response
```json
{
    "message": "message"
}
```
### /api/profile/user/details/ [GET, PUT] (authentication required)
#### Request
```json
{
    "name": "name", // optional
    "lang": "lang", // optional
    "image": "image", // optional
}
```
#### Response
```json
{
    "name": "name",
    "email": "email",
    "lang": "lang",
    "image": "image"
}
```
### /api/profile/business/details/ [GET, PUT] (authentication required)
#### Request
```json
{
    "name": "name", // optional
    "lang": "lang", // optional
    "image": "image", // optional
}
```
#### Response
```json
{
    "name": "name",
    "email": "email",
    "lang": "lang",
    "image": "image"
}
```

### /api/profile/business/legal-info/ [GET, PUT] (authentication required)
#### Request
```json
{
    "full_business_name": "full_business_name",
    "registered_address": "registered_address",
    "operational_address": "operational_address",
    "offical_phone_number": "offical_phone_number",
    "offical_email": "offical_email@example.com",
    "primary_contact_name": "primary_contact_name",
    "primary_contact_phone_number": "primary_contact_phone_number",
    "primary_contact_email": "primary_contact_email@example.com",
    "primary_contact_position": "primary_contact_position",
    "cr_number": "cr_number",
    "vat_number": "vat_number",
    "mwan_number": "mwan_number", // optional
    "legal_document": {
        "cr_copy": "cr_copy",
        "vat_copy": "vat_copy",
        "mwan_copy": "mwan_copy" // optional
    }
}
```
#### Response
```json
{
    "full_business_name": "full_business_name",
    "registered_address": "registered_address",
    "operational_address": "operational_address",
    "offical_phone_number": "offical_phone_number",
    "offical_email": "offical_email@example.com",
    "primary_contact_name": "primary_contact_name",
    "primary_contact_phone_number": "primary_contact_phone_number",
    "primary_contact_email": "primary_contact_email@example.com",
    "primary_contact_position": "primary_contact_position",
    "cr_number": "cr_number",
    "vat_number": "vat_number",
    "mwan_number": "mwan_number",
    "status": "status",
    "rejection_reason": "rejection_reason",
    "legal_document": {
        "cr_copy": "cr_copy",
        "vat_copy": "vat_copy",
        "mwan_copy": "mwan_copy"
    }
}
```
### /api/profile/email-change/ [POST] (authentication required)
#### Request
```json
{
    "new_email": "new_email",
    "new_email_confirm": "new_email_confirm",
    "password": "password",
    "otp": "otp" // conditional
}
```
#### Response
```json
{
    "message": "message"
}
```
### /api/profile/password-change/ [POST] (authentication required)
#### Request
```json
{
    "current_password": "current_password",
    "new_password": "new_password",
    "new_password_confirm": "new_password_confirm",
    "otp": "otp" // conditional
}
```
#### Response
```json
{
    "message": "message"
}
```
### /api/profile/contact-change/ [POST] (authentication required) //not implemented
#### Request
```json
{
    "new_phone": "new_phone",
    "sms_otp": "sms_otp" // conditional
}
```
### /api/profile/account-delete/ [DELETE] (authentication required)
#### Request
```json
{
    "password": "password"
}
```
#### Response
```json
{
    "message": "message"
}
```


## Inventory API endpoints
### /api/inventory/items/?query=""&group_type=""&category=""&seller=""&most_sold="true/false" [GET] (authentication required)
#### Request (No body)
#### Response
```json
[
    {
    "id": 1,
    "name": "Item 1",
    "images": [],
    "price": "30.00",
    "price_unit": "20",
    "category": 1,
    "mds_document": null,
    "category_type": "product",
    "extra_fields": [
        {
            "value": "50",
            "type": {
                "name": "Thickness",
                "icon": null
            }
        }
    ],
    "sub_items": [
        {
            "value": "Hi"
        }
    ],
    "owner_image": null,
    "description": null,
    "address_line1": "address_line1",
    "address_line2": null,
    "city": "city 1",
    "province": "province 1",
    "zip_code": "zip_code 1",
    "country": "country 1",
    "on_site_pickup": false,
    "rent_item_info": {
                "id": 1,
                "rent_item_unit_info": [
                    {
                        "rent_item_unit_documents": [
                            {
                                "name": "Driver license",
                                "expiry_date": "2026-01-28",
                                "file": ""
                            },
                            {
                                "name": "Aramco approved certificate",
                                "expiry_date": "2028-01-28",
                                "file": ""
                            }
                        ],
                        "plate_number": "VVK 2432"
                    },
                    {
                        "rent_item_unit_documents": [
                            {
                                "name": "Driver license",
                                "expiry_date": "2026-01-31",
                                "file": ""
                            }
                        ],
                        "plate_number": "SGR 5344"
                    }
                ],
                "model_year": "2005",
                "with_driver": False,
                "delivery_charges": "0.00",
                "make": "Toyota",
                "model": "Corolla",
                "price_charged_per": "DAY"
            }
    }
]
```

### /api/inventory/items/[ID] [GET]
#### Request (No body)
#### Response
```json
{
    "id": 1,
    "name": "Item 1",
    "images": [],
    "price": "30.00",
    "price_unit": "20",
    "category": 1,
    "mds_document": null,
    "category_type": "product",
    "extra_fields": [
        {
            "value": "50",
            "type": {
                "name": "Thickness",
                "icon": null
            }
        }
    ],
    "sub_items": [
        {
            "value": "Hi"
        }
    ],
    "owner_image": null,
    "description": null,
    "address_line1": "address_line1",
    "address_line2": null,
    "city": "city 1",
    "province": "province 1",
    "zip_code": "zip_code 1",
    "country": "country 1",
    "on_site_pickup": false,
    "quantity": 3
}
```

### /api/inventory/user/items/?query=""&category_group="" [GET] (authentication required)
#### Request (No body)
#### Response
```json
[
    {
    "id": 1,
    "name": "Item 1",
    "images": [],
    "price": "30.00",
    "price_unit": "20",
    "category": 1,
    "mds_document": null,
    "category_type": "product",
    "extra_fields": [
        {
            "value": "50",
            "type": {
                "name": "Thickness",
                "icon": null
            }
        }
    ],
    "sub_items": [
        {
            "value": "Hi"
        }
    ],
    "owner_image": null,
    "description": null,
    "address_line1": "address_line1",
    "address_line2": null,
    "city": "city 1",
    "province": "province 1",
    "zip_code": "zip_code 1",
    "country": "country 1",
    "on_site_pickup": false,
    "quantity": 3
    }
]
```

### /api/inventory/user/items/[ID] [GET]
#### Request (No body)
#### Response
```json
{
    "id": 1,
    "name": "Item 1",
    "images": [],
    "price": "30.00",
    "price_unit": "20",
    "category": 1,
    "mds_document": null,
    "category_type": "product",
    "extra_fields": [
        {
            "value": "50",
            "type": {
                "name": "Thickness",
                "icon": null
            }
        }
    ],
    "sub_items": [
        {
            "value": "Hi"
        }
    ],
    "owner_image": null,
    "description": null,
    "address_line1": "address_line1",
    "address_line2": null,
    "city": "city 1",
    "province": "province 1",
    "zip_code": "zip_code 1",
    "country": "country 1",
    "on_site_pickup": false,
    "quantity": 3
}
```





## BMS API endpoints
### /api/billing/orders/?query=""&is_delivery=""&group_type=""&category_group=""&category=""&status=""&sort="" [GET] (authentication required)
#### Request (No body)
#### Response
```json
[
    {
            "id": "feba31f3-91eb-4de0-95b8-f30f94f39569",
            "items": [
                {
                    "name": "Steel inspection 1",
                    "price": "30.00",
                    "category": {
                        "id": 3,
                        "name": "Steel inspection",
                        "name_ar": "Steel inspection",
                        "extra_field_types": [],
                        "sub_item_type": "fleet"
                    },
                    "mds_document": null,
                    "extra_fields": [],
                    "description": null,
                    "address_line1": "address_line1",
                    "address_line2": null,
                    "city": "city 1",
                    "province": "province 1",
                    "zip_code": "zip_code 1",
                    "country": "country 1",
                    "on_site_pickup": false,
                    "quantity": 3
                }
            ],
            "buyer": {
                "name": "New company",
                "email": "sanny@gmail.com",
                "contact_number": "+966591186753",
                "cr_number": "6535085453"
            },
            "number": "0000",
            "status": "pending",
            "created_at": "2025-01-21T17:20:16.075973+03:00",
            "is_delivery": false,
            "delivery_address_line1": "jhhh",
            "delivery_address_line2": null,
            "delivery_city": "Cii",
            "delivery_province": "jhj",
            "delivery_zip_code": "yyu",
            "delivery_country": "hhh",
            "delivery_charges": "22.00",
            "total_price": null,
            "total_discount": null,
            "total_price_after_discount": null,
            "tax_amount": null,
            "total_with_tax": null,
            "zatca_qr": null,
            "base64_invoice": null,
            "invoice_hash": null
        }
]
```
### /api/billing/orders/ [POST] (authentication required)
#### Request
```json
{
    "number" : "0000",
    "delivery_address_line1": "jhhh",
    "delivery_city" : "Cii",
    "delivery_province" : "jhj",
    "delivery_zip_code" : "yyu",
    "delivery_country" : "hhh",
    "delivery_charges" : 22,
    "type" : "delivery",
    "items" : [6, 7]
    // "additonal_services" : [{"id": 1 , "additonal": [2.3] }]
    // "items" : [{"id": 1 , "additonal": [2.3] }, {"id": 4 }]
}
```
#### Response
```json
{
        "id": "8933e81b-b9bf-4932-8cfb-ce6ae79b8027",
        "items": [
            {
                "name": "Steel inspection 1",
                "price": "30.00",
                "category": {
                    "id": 3,
                    "name": "Steel inspection",
                    "name_ar": "Steel inspection",
                    "extra_field_types": [],
                    "sub_item_type": "fleet"
                },
                "mds_document": null,
                "extra_fields": [],
                "description": null,
                "address_line1": "address_line1",
                "address_line2": null,
                "city": "city 1",
                "province": "province 1",
                "zip_code": "zip_code 1",
                "country": "country 1",
                "on_site_pickup": false,
                "quantity": 3
            }
        ],
        "buyer": {
            "name": "New company",
            "email": "sanny@gmail.com",
            "contact_number": "+966591186753",
            "cr_number": "6535085453"
        },
        "number": "0000",
        "status": "pending",
        "created_at": "2025-01-22T11:12:32.447006+03:00",
        "is_delivery": false,
        "delivery_address_line1": "jhhh",
        "delivery_address_line2": null,
        "delivery_city": "Cii",
        "delivery_province": "jhj",
        "delivery_zip_code": "yyu",
        "delivery_country": "hhh",
        "delivery_charges": "22.00",
        "total_price": null,
        "total_discount": null,
        "total_price_after_discount": null,
        "tax_amount": null,
        "total_with_tax": null,
        "zatca_qr": null,
        "base64_invoice": null,
        "invoice_hash": null
    }
```

### /api/billing/ [GET] (authentication required)
#### Request (No body)
#### Response
```json
[
    {
            "id": "e6e53ec6-0a37-42f1-855d-dbe771ea9bf5",
            "items": [
                {
                    "name": "Item 2",
                    "price": "30.00",
                    "category": {
                        "id": 1,
                        "name": "Dry plastic subcategory",
                        "name_ar": "Dry plastic subcategory",
                        "extra_field_types": [
                            {
                                "name": "Thickness",
                                "icon": null
                            }
                        ],
                        "sub_item_type": "fleet"
                    },
                    "mds_document": "/media/company_docs/New%20company/mds/download.jpeg",
                    "extra_fields": [
                        {
                            "value": "50",
                            "type": {
                                "name": "Thickness",
                                "icon": null
                            }
                        }
                    ],
                    "description": null,
                    "address_line1": "address_line1",
                    "address_line2": null,
                    "city": "city 1",
                    "province": "province 1",
                    "zip_code": "zip_code 1",
                    "country": "country 1",
                    "on_site_pickup": false,
                    "quantity": 3
                }
            ],
            "bill_type": "taxinvoice",
            "buyer": {
                "name": "New company",
                "email": "sanny@gmail.com",
                "contact_number": "+966591186753",
                "cr_number": "6535085453"
            },
            "number": "0000",
            "created_at": "2025-01-21T16:56:26.986224+03:00",
            "is_delivery": true,
            "delivery_address_line1": "jhhh",
            "delivery_address_line2": null,
            "delivery_city": "Cii",
            "delivery_province": "jhj",
            "delivery_zip_code": "yyu",
            "delivery_country": "hhh",
            "total_price": null,
            "total_discount": null,
            "total_price_after_discount": null,
            "tax_amount": null,
            "total_with_tax": null,
            "zatca_qr": null,
            "base64_invoice": null,
            "invoice_hash": null
        }
]
```

### /api/billing/[UUID] [GET] (authentication required)
#### Request (No body)
#### Response
```json
{
            "id": "e6e53ec6-0a37-42f1-855d-dbe771ea9bf5",
            "items": [
                {
                    "name": "Item 2",
                    "price": "30.00",
                    "category": {
                        "id": 1,
                        "name": "Dry plastic subcategory",
                        "name_ar": "Dry plastic subcategory",
                        "extra_field_types": [
                            {
                                "name": "Thickness",
                                "icon": null
                            }
                        ],
                        "sub_item_type": "fleet"
                    },
                    "mds_document": "/media/company_docs/New%20company/mds/download.jpeg",
                    "extra_fields": [
                        {
                            "value": "50",
                            "type": {
                                "name": "Thickness",
                                "icon": null
                            }
                        }
                    ],
                    "description": null,
                    "address_line1": "address_line1",
                    "address_line2": null,
                    "city": "city 1",
                    "province": "province 1",
                    "zip_code": "zip_code 1",
                    "country": "country 1",
                    "on_site_pickup": false,
                    "quantity": 3
                }
            ],
            "bill_type": "taxinvoice",
            "buyer": {
                "name": "New company",
                "email": "sanny@gmail.com",
                "contact_number": "+966591186753",
                "cr_number": "6535085453"
            },
            "number": "0000",
            "created_at": "2025-01-21T16:56:26.986224+03:00",
            "is_delivery": true,
            "delivery_address_line1": "jhhh",
            "delivery_address_line2": null,
            "delivery_city": "Cii",
            "delivery_province": "jhj",
            "delivery_zip_code": "yyu",
            "delivery_country": "hhh",
            "total_price": null,
            "total_discount": null,
            "total_price_after_discount": null,
            "tax_amount": null,
            "total_with_tax": null,
            "zatca_qr": null,
            "base64_invoice": null,
            "invoice_hash": null
        }
```


## DMS API endpoints
### /api/documents/?query=""&type=""&start_date=""&end_date="" [GET] (authentication required)
#### Request (No body)
#### Response
```json
[
    {
        "id": "313c35ca-7c4a-486f-9f65-8c1bd83ebf60",
        "order_item": {
            "id": 15,
            "name": "Item from another",
            "price": "30.00",
            "category": {
                "id": 3,
                "name": "Steel inspection",
                "name_ar": "Steel inspection",
                "extra_field_types": [],
                "sub_item_type": "fleet"
            },
            "mds_document": null,
            "extra_fields": [],
            "description": null,
            "address_line1": "address_line1",
            "address_line2": null,
            "city": "city 1",
            "province": "province 1",
            "zip_code": "zip_code 1",
            "country": "country 1",
            "on_site_pickup": false,
            "quantity": 2,
            "order_quantity": 1
        },
        "type": "reports",
        "uploaded_at": "2025-01-23T11:46:38.272381+03:00",
        "file": "file"
    },
]
```
### /api/documents/ [POST] (authentication required)
#### Request (No body)
```json
{
        "type": "reports",
        "file": "file",
        "order_item": 5
    },
```
#### Response
```json
{
        "id": "313c35ca-7c4a-486f-9f65-8c1bd83ebf60",
        "order_item": {
            "id": 15,
            "name": "Item from another",
            "price": "30.00",
            "category": {
                "id": 3,
                "name": "Steel inspection",
                "name_ar": "Steel inspection",
                "extra_field_types": [],
                "sub_item_type": "fleet"
            },
            "mds_document": null,
            "extra_fields": [],
            "description": null,
            "address_line1": "address_line1",
            "address_line2": null,
            "city": "city 1",
            "province": "province 1",
            "zip_code": "zip_code 1",
            "country": "country 1",
            "on_site_pickup": false,
            "quantity": 2,
            "order_quantity": 1
        },
        "type": "reports",
        "uploaded_at": "2025-01-23T11:46:38.272381+03:00",
        "file": "file"
    },
```