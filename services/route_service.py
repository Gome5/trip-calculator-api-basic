import os

import requests


class ExternalServiceError(RuntimeError):
    pass


class RouteService:
    def __init__(self):
        self.geocoder_url = os.getenv("GEOCODER_URL", "https://nominatim.openstreetmap.org/search")
        self.router_url = os.getenv("ROUTER_URL", "https://router.project-osrm.org/route/v1/driving")
        self.timeout = float(os.getenv("EXTERNAL_API_TIMEOUT", "8"))
        self.headers = {"User-Agent": os.getenv("EXTERNAL_API_USER_AGENT", "trip-calculator-academic/1.0")}

    def _geocode(self, place):
        response = requests.get(
            self.geocoder_url,
            params={"q": place, "format": "jsonv2", "limit": 1},
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            raise ExternalServiceError(f"Could not geocode location: {place}")
        return float(results[0]["lon"]), float(results[0]["lat"])

    def get_route(self, origin, destination):
        try:
            origin_lon, origin_lat = self._geocode(origin)
            destination_lon, destination_lat = self._geocode(destination)
            response = requests.get(
                f"{self.router_url}/{origin_lon},{origin_lat};{destination_lon},{destination_lat}",
                params={"overview": "false"},
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            route = response.json().get("routes", [None])[0]
            if not route or "distance" not in route or "duration" not in route:
                raise ExternalServiceError("Route provider returned no usable route")
            return {
                "distance_km": round(float(route["distance"]) / 1000, 2),
                "duration_minutes": round(float(route["duration"]) / 60),
            }
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            raise ExternalServiceError("Route provider is unavailable") from exc


route_service = RouteService()
