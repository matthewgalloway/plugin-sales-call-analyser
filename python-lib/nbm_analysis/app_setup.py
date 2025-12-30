from flask import Flask, session
from flask_cors import CORS
import secrets

from nbm_analysis.utils.logging_utils import get_logger
from nbm_analysis.routes.api import api_blueprint


logger = get_logger(__name__)


def create_app(app: Flask) -> Flask:

    CORS(app)

    # Configure file upload settings
    app.config.update(
        MAX_CONTENT_LENGTH=5 * 1024 * 1024  # 5MB max file size
    )

    app.register_blueprint(api_blueprint)

    return app
