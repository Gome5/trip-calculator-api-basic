import os
from pathlib import Path

from dotenv import load_dotenv
from flask import jsonify
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI

from database.database import db
from routes.trip_routes import trip_bp

load_dotenv()
info = Info(title="Trip Calculator API", version="1.0.0")


def create_app(test_config=None):
	app = OpenAPI(
		__name__,
		info=info,
		doc_prefix="/openapi",
		doc_url="/openapi.json",
		validation_error_status=400,
	)
	database_url = os.getenv("DATABASE_URL", "sqlite:///trip_calculator.db")
	if database_url.startswith("sqlite:////data/"):
		Path("/data").mkdir(parents=True, exist_ok=True)
	app.config.from_mapping(
		SQLALCHEMY_DATABASE_URI=database_url,
		SQLALCHEMY_TRACK_MODIFICATIONS=False,
		JSON_SORT_KEYS=False,
	)
	if test_config:
		app.config.update(test_config)

	db.init_app(app)
	origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",")
	CORS(app, resources={r"/api/*": {"origins": [origin.strip() for origin in origins]}})
	app.register_api(trip_bp, url_prefix="/api")

	@app.get("/")
	def home():
		return jsonify(
			{
				"service": "trip-calculator-api",
				"message": "API para planejamento e estimativa de custos de viagens.",
				"health": "/health",
				"base_url": "/api",
			}
		)

	@app.get("/health")
	def health():
		return jsonify({"status": "ok", "service": "trip-calculator-api"})

	with app.app_context():
		from models.trip import Trip  # noqa: F401

		db.create_all()
	return app


app = create_app()


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
