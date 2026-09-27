from flask import jsonify, request
from flask_openapi3 import APIBlueprint, RawModel
from pydantic import BaseModel

from database.database import db
from models.trip import Trip
from services.calculation_service import calculate_costs
from services.route_service import ExternalServiceError, route_service
from services.weather_service import weather_service
from utils.validators import ValidationError, validate_trip_payload


trip_bp = APIBlueprint("trips", __name__)


class TripPath(BaseModel):
    trip_id: int


def _error_response(message, status, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return jsonify(body), status


def _request_data(payload, include_route=True):
    normalized = validate_trip_payload(payload)
    route = route_service.get_route(normalized["origin"], normalized["destination"]) if include_route else {}
    costs = calculate_costs(
        route["distance_km"],
        normalized["fuel_consumption"],
        normalized["fuel_price"],
        normalized["tolls"],
    )
    try:
        weather = weather_service.get_weather(normalized["destination"], normalized["travel_date"])
    except Exception:
        weather = {"weather": None, "temperature": None}
    return {**normalized, **route, **costs, **weather}


def _trip_from_data(data):
    return Trip(
        origin=data["origin"],
        destination=data["destination"],
        travel_date=data["travel_date"],
        distance_km=data["distance_km"],
        duration_minutes=data["duration_minutes"],
        fuel_consumption=data["fuel_consumption"],
        fuel_price=data["fuel_price"],
        fuel_needed=data["fuel_needed"],
        fuel_cost=data["fuel_cost"],
        tolls=data["tolls"],
        total_cost=data["total_cost"],
        weather=data.get("weather"),
        temperature=data.get("temperature"),
    )


@trip_bp.get("/trips")
def list_trips():
    """List saved trips with optional origin, destination and sort filters."""
    query = Trip.query
    origin = request.args.get("origin")
    destination = request.args.get("destination")
    sort = request.args.get("sort")
    if origin:
        query = query.filter(Trip.origin.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(Trip.destination.ilike(f"%{destination}%"))
    if sort == "total_cost":
        query = query.order_by(Trip.total_cost.asc())
    elif sort == "date":
        query = query.order_by(Trip.travel_date.asc())
    else:
        query = query.order_by(Trip.created_at.desc())
    trips = query.all()
    return jsonify({"data": [trip.to_dict() for trip in trips], "total": len(trips)})


@trip_bp.get("/trips/<int:trip_id>")
def get_trip(path: TripPath):
    """Return one saved trip by id."""
    trip = db.session.get(Trip, path.trip_id)
    if not trip:
        return _error_response("Trip not found", 404)
    return jsonify(trip.to_dict())


@trip_bp.post("/trips/calculate")
def calculate_trip(raw: RawModel):
    """Calculate a trip without persisting it."""
    try:
        result = _request_data(request.get_json(silent=True))
        result.pop("travel_date", None)
        return jsonify(result)
    except ValidationError as error:
        return _error_response("Validation error", 400, error.errors)
    except ExternalServiceError as error:
        return _error_response(str(error), 502)
    except (KeyError, TypeError, ZeroDivisionError) as error:
        return _error_response(f"Unable to calculate trip: {error}", 400)


@trip_bp.post("/trips")
def create_trip(raw: RawModel):
    """Calculate and persist a new trip."""
    try:
        data = _request_data(request.get_json(silent=True))
        trip = _trip_from_data(data)
        db.session.add(trip)
        db.session.commit()
        return jsonify({"message": "Trip created successfully", "trip": trip.to_dict()}), 201
    except ValidationError as error:
        return _error_response("Validation error", 400, error.errors)
    except ExternalServiceError as error:
        return _error_response(str(error), 502)
    except (KeyError, TypeError, ZeroDivisionError) as error:
        db.session.rollback()
        return _error_response(f"Unable to create trip: {error}", 400)


@trip_bp.put("/trips/<int:trip_id>")
def update_trip(path: TripPath, raw: RawModel):
    """Update a trip and recalculate its costs."""
    trip = db.session.get(Trip, path.trip_id)
    if not trip:
        return _error_response("Trip not found", 404)
    payload = request.get_json(silent=True)
    try:
        allowed = {"origin", "destination", "travel_date", "fuel_consumption", "fuel_price", "tolls"}
        unknown = set(payload or {}) - allowed
        if unknown:
            return _error_response("Validation error", 400, {"fields": f"Unknown fields: {', '.join(sorted(unknown))}"})
        values = {
            "origin": trip.origin,
            "destination": trip.destination,
            "travel_date": trip.travel_date.isoformat(),
            "fuel_consumption": trip.fuel_consumption,
            "fuel_price": trip.fuel_price,
            "tolls": trip.tolls,
        }
        values.update(payload or {})
        data = _request_data(values)
        for field, value in data.items():
            if hasattr(trip, field) and field != "id":
                setattr(trip, field, value)
        db.session.commit()
        return jsonify(trip.to_dict())
    except ValidationError as error:
        return _error_response("Validation error", 400, error.errors)
    except ExternalServiceError as error:
        return _error_response(str(error), 502)
    except (KeyError, TypeError, ZeroDivisionError) as error:
        db.session.rollback()
        return _error_response(f"Unable to update trip: {error}", 400)


@trip_bp.delete("/trips/<int:trip_id>")
def delete_trip(path: TripPath):
    """Delete a saved trip."""
    trip = db.session.get(Trip, path.trip_id)
    if not trip:
        return _error_response("Trip not found", 404)
    db.session.delete(trip)
    db.session.commit()
    return "", 204