"""Flask application entrypoint."""

from __future__ import annotations

import json
import logging

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from auth import require_api_key
from config import get_settings
from extract import run_extraction
from sec import warm_ticker_cache
from validation import parse_extract_request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
app = Flask(__name__)

CORS(
    app,
    origins=settings.frontend_origins,
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[settings.default_rate_limit],
    storage_uri="memory://",
)


@app.route("/health", methods=["GET"])
@limiter.exempt
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/extract", methods=["POST"])
@limiter.limit(settings.extract_rate_limit)
def extract_endpoint():
    if err := require_api_key(request):
        return err

    payload, err = parse_extract_request(request.get_json(silent=True))
    if err:
        return err

    def generate():
        for message in run_extraction(payload):
            yield json.dumps(message) + "\n"

    return Response(generate(), mimetype="application/x-ndjson")


def create_app() -> Flask:
    """Factory used by WSGI servers / tests."""
    return app


if __name__ == "__main__":
    warm_ticker_cache()
    app.run(debug=settings.flask_debug, host=settings.flask_host, port=settings.flask_port)
