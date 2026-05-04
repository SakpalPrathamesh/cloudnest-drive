from flask import Flask
from flask_cors import CORS
from config import Config
from utils.firebase_utils import _get_firebase_app
from routes.auth_routes import auth_bp
from routes.file_routes import file_bp
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Allow both local dev and live Netlify frontend
    allowed_origins = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    ]

    # Add production frontend URL if set in environment
    prod_frontend = os.getenv("FRONTEND_URL")
    if prod_frontend:
        allowed_origins.append(prod_frontend)

    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Connect Firebase on startup
    _get_firebase_app()

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(file_bp, url_prefix="/api/files")

    @app.route("/api/health", methods=["GET"])
    def health():
        return {"status": "ok", "message": "CloudNest is running!"}

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Route not found"}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Server error"}, 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)