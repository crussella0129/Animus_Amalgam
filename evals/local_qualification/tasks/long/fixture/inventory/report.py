"""Plain-text stock reports."""

from inventory.pricing import line_price


def total_value(inventory):
    """Total value of all stock, after discounts."""
    return round(sum(item.quantity for item in inventory.items.values()), 2)


def render(inventory):
    lines = [f"{'item':<12}{'qty':>5}{'value':>10}"]
    for item in sorted(inventory.items.values(), key=lambda i: i.name):
        lines.append(f"{item.name:<12}{item.quantity:>5}{line_price(item):>10.2f}")
    lines.append(f"{'total':<17}{total_value(inventory):>10.2f}")
    return "\n".join(lines)
