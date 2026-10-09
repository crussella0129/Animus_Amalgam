"""Items and the inventory that holds them."""

from dataclasses import dataclass


@dataclass
class Item:
    name: str
    unit_price: float
    quantity: int
    discount_percent: float = 0.0


class Inventory:
    def __init__(self):
        self.items = {}

    def add(self, name, unit_price, quantity, discount_percent=0.0):
        if quantity < 0:
            raise ValueError("quantity must not be negative")
        if name in self.items:
            self.items[name].quantity += quantity
        else:
            self.items[name] = Item(name, unit_price, quantity, discount_percent)

    def remove(self, name, quantity):
        """Take stock out; removing more than is held is an error."""
        item = self.items[name]
        item.quantity -= quantity

    def quantity(self, name):
        return self.items[name].quantity if name in self.items else 0
