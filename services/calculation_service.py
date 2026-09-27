from decimal import Decimal, ROUND_HALF_UP


def _money(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_costs(distance_km, fuel_consumption, fuel_price, tolls):
    fuel_needed = round(distance_km / fuel_consumption, 2)
    fuel_cost = fuel_needed * fuel_price
    total_cost = fuel_cost + tolls
    return {
        "fuel_needed": fuel_needed,
        "fuel_cost": _money(fuel_cost),
        "total_cost": _money(total_cost),
    }
