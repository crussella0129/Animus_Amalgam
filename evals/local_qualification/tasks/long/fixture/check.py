"""Run the project's checks and print one PASS/FAIL line per check."""

import sys

from inventory import Inventory, line_price, total_value
from inventory.models import Item


def check_remove_guard():
    inv = Inventory()
    inv.add("bolt", 0.5, 3)
    try:
        inv.remove("bolt", 5)
    except ValueError:
        return inv.quantity("bolt") == 3
    return False


def check_discount():
    return line_price(Item("nut", 2.0, 10, discount_percent=25)) == 15.0


def check_total():
    inv = Inventory()
    inv.add("nut", 2.0, 10, discount_percent=25)
    inv.add("washer", 0.1, 50)
    return total_value(inv) == 20.0


CHECKS = [check_remove_guard, check_discount, check_total]


def main():
    failed = 0
    for check in CHECKS:
        try:
            ok = check()
        except Exception as exc:  # report, never crash the runner
            ok = False
            print(f"FAIL {check.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
            continue
        print(f"{'PASS' if ok else 'FAIL'} {check.__name__}")
        failed += not ok
    print(f"{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
