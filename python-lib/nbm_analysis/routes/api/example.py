from flask import Blueprint, g, request, jsonify, Response

from nbm_analysis.utils.logging_utils import get_logger

example_blueprint = Blueprint("example", __name__, url_prefix="/example")

logger = get_logger(__name__)


@example_blueprint.route("/get_hello_world")
def get_hello_world() -> Response:
    hello_world = "Hello, World!"

    return jsonify(hello_world)
