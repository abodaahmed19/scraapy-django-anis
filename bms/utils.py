def validate_credit_card(card_number):
    if not card_number:
        return False
    if len(card_number) != 16:
        return False
    if not card_number.isdigit():
        return False
    # validate mastercard or visa
    if not (card_number.startswith('4') or card_number.startswith('5')):
        return False
    # validate checksum
    total = 0
    for i, digit in enumerate(card_number[::-1]):
        if i % 2 == 0:
            total += int(digit)
        else:
            total += sum(int(x) for x in str(int(digit) * 2))
    if total % 10 != 0:
        return False
    return True

def get_shipping_options(shipping_cost=None):
    standard_shipping_price = shipping_cost if shipping_cost is not None else None
    return [
        {
            'id': 1,
            'name': 'Standard Shipping',
            'name_ar': 'الشحن القياسي',
            'price': standard_shipping_price,
            'detail': 'Your order will be delivered to you within 3-5 business days.',
            'detail_ar': 'سيتم توصيل طلبك إليك خلال 3-5 أيام عمل.',
        },
        {
            'id': 2,
            'name': 'Pick Up',
            'name_ar': 'استلام',
            'price': 0,
            'detail': 'You will be able to pick up your order from the store in 1 business day.',
            'detail_ar': 'سيتمكنك من استلام طلبك من المتجر في يوم عمل واحد.',
        },
    ]


def order_item_report_path(instance, filename):
    return f'order_item_reports/{instance.order_item.order.id}/{filename}'
