from flask import Blueprint, request, jsonify, Response
from datetime import datetime
import os
from nbm_analysis.utils.logging_utils import get_logger
from nbm_analysis.utils.file_processor import FileProcessor

# Use mock client for local development
if os.getenv('FLASK_ENV') == 'development' or not os.getenv('DATAIKU_LLM_ID'):
    from nbm_analysis.utils.llm_client_mock import SalesAnalysisLLM
    logger = get_logger(__name__)
    logger.info("Using MOCK LLM client for local development")
else:
    from nbm_analysis.utils.llm_client import SalesAnalysisLLM

analysis_blueprint = Blueprint("analysis", __name__, url_prefix="/analysis")
logger = get_logger(__name__)


@analysis_blueprint.route("/analyze", methods=["POST"])
def analyze_transcript() -> Response:
    """API endpoint to analyze uploaded transcript file"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        # Validate file
        is_valid, message = FileProcessor.validate_file(file)
        if not is_valid:
            logger.warning(f"File validation failed: {message}")
            return jsonify({"error": message}), 400

        # Read file content
        content = FileProcessor.read_file_content(file)
        if not content:
            logger.error(f"Could not read file content: {file.filename}")
            return jsonify({"error": "Could not read file content. Please ensure it's a valid .txt or .docx file"}), 400

        # Create analysis
        start_time = datetime.now()

        llm_client = SalesAnalysisLLM()

        # Create evidence registry
        evidence_data = llm_client.create_evidence_registry(content)
        if "error" in evidence_data:
            logger.error(f"Evidence registry failed: {evidence_data['error']}")
            return jsonify({"error": f"Analysis failed: {evidence_data['error']}"}), 500

        # Create analysis
        analysis_data = llm_client.create_analysis(evidence_data)
        if "error" in analysis_data:
            logger.error(f"Analysis failed: {analysis_data['error']}")
            return jsonify({"error": f"Analysis failed: {analysis_data['error']}"}), 500

        # Log successful analysis
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Analysis completed in {processing_time:.2f}s")

        # Combine results
        result = {**evidence_data, **analysis_data, "is_sample": False}
        return jsonify(result)

    except Exception as e:
        logger.error(f"Unexpected error in analysis: {str(e)}")
        return jsonify({"error": "Analysis failed due to an unexpected error. Please try again."}), 500


@analysis_blueprint.route("/analyze-sample", methods=["POST"])
def analyze_sample() -> Response:
    """API endpoint to analyze sample transcript"""
    try:
        # Load sample transcript
        content = FileProcessor.load_sample_transcript()
        if not content:
            logger.error("Could not load sample transcript")
            return jsonify({"error": "Sample transcript not available. Please try uploading your own file."}), 400

        # Create analysis
        start_time = datetime.now()

        llm_client = SalesAnalysisLLM()

        # Create evidence registry
        evidence_data = llm_client.create_evidence_registry(content, user_email="sample_user")
        if "error" in evidence_data:
            logger.error(f"Sample evidence registry failed: {evidence_data['error']}")
            return jsonify({"error": f"Sample analysis failed: {evidence_data['error']}"}), 500

        # Create analysis
        analysis_data = llm_client.create_analysis(evidence_data, user_email="sample_user")
        if "error" in analysis_data:
            logger.error(f"Sample analysis failed: {analysis_data['error']}")
            return jsonify({"error": f"Sample analysis failed: {analysis_data['error']}"}), 500

        # Log successful analysis
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Sample analysis completed in {processing_time:.2f}s")

        # Combine results and add sample indicator
        result = {**evidence_data, **analysis_data, "is_sample": True}
        return jsonify(result)

    except Exception as e:
        logger.error(f"Unexpected error in sample analysis: {str(e)}")
        return jsonify({"error": "Sample analysis failed due to an unexpected error. Please try again."}), 500


@analysis_blueprint.route("/deal-review", methods=["POST"])
def generate_deal_review() -> Response:
    """API endpoint to create deal review from existing analysis"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        evidence_registry = data.get('evidence_registry', {})
        analysis_data = data.get('analysis_data', {})

        if not evidence_registry or not analysis_data:
            return jsonify({"error": "Missing analysis data for deal review"}), 400

        # Create deal review
        llm_client = SalesAnalysisLLM()
        deal_review_data = llm_client.create_deal_review(evidence_registry, analysis_data)

        if "error" in deal_review_data:
            logger.error(f"Deal review failed: {deal_review_data['error']}")
            return jsonify({"error": f"Deal review failed: {deal_review_data['error']}"}), 500

        logger.info("Deal review completed")
        return jsonify(deal_review_data)

    except Exception as e:
        logger.error(f"Unexpected error in deal review endpoint: {str(e)}")
        return jsonify({"error": "Deal review failed due to an unexpected error. Please try again."}), 500
