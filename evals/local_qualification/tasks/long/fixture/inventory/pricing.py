"""Prices for inventory lines."""


def line_price(item):
    """Value of one inventory line after the item's percentage discount."""
    discounted = item.unit_price * item.discount_percent / 100
    return round(discounted * item.quantity, 2)
