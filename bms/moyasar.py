import requests
from django.conf import settings

def process_payment_token(amount, token):
    url = 'https://api.moyasar.com/v1/payments'
    headers = {
            'Authorization': f'Basic {settings.MOYASAR_API_KEY}',
            'Content-Type': 'application/X-www-form-urlencoded'
        }
    data = {
            'amount': amount,
            'callback_url': settings.MOYASAR_CALLBACK_URL,
            'source[type]': 'token',
            'source[token]': token,
        }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise ValueError('Payment failed')
    return response.json()

def process_payment_card(amount, name, number, month, year, cvc, save_card=False):
    url = 'https://api.moyasar.com/v1/payments'
    headers = {
            'Authorization': f'Basic {settings.MOYASAR_API_KEY}',
            'Content-Type': 'application/X-www-form-urlencoded'
        }
    data = {
            'amount': amount,
            'callback_url': settings.MOYASAR_CALLBACK_URL,
            'source[type]': 'creditcard',
            'source[name]': name,
            'source[number]': number,
            'source[month]': month,
            'source[year]': year,
            'source[cvc]': cvc,
            'source[save_card]': save_card,
        }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 201:
        raise ValueError('Payment failed')
    return response.json()

def fetch_payment(payment_id):
    url = f'https://api.moyasar.com/v1/payments/{payment_id}'
    headers = {
            'Authorization': f'Basic {settings.MOYASAR_API_KEY}',
        }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError('Payment not found')
    return response.json()
