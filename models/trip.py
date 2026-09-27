from datetime import datetime, timezone

from database.database import db


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    fuel_consumption = db.Column(db.Float, nullable=False)
    fuel_price = db.Column(db.Float, nullable=False)
    fuel_needed = db.Column(db.Float, nullable=False)
    fuel_cost = db.Column(db.Float, nullable=False)
    tolls = db.Column(db.Float, nullable=False, default=0)
    total_cost = db.Column(db.Float, nullable=False)
    weather = db.Column(db.String(120), nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "origin": self.origin,
            "destination": self.destination,
            "travel_date": self.travel_date.isoformat(),
            "distance_km": self.distance_km,
            "duration_minutes": self.duration_minutes,
            "fuel_consumption": self.fuel_consumption,
            "fuel_price": self.fuel_price,
            "fuel_needed": self.fuel_needed,
            "fuel_cost": self.fuel_cost,
            "tolls": self.tolls,
            "total_cost": self.total_cost,
            "weather": self.weather,
            "temperature": self.temperature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
