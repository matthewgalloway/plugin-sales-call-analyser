from flask import Blueprint

from nbm_analysis.routes.api.example import example_blueprint
from nbm_analysis.routes.api.analysis import analysis_blueprint

api_blueprint = Blueprint("api", __name__, url_prefix="/api")
api_blueprint.register_blueprint(example_blueprint)
api_blueprint.register_blueprint(analysis_blueprint)
