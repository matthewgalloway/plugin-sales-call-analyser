from flask import Blueprint, request, jsonify, Response, stream_with_context
from datetime import datetime
import os
import json
from nbm_analysis.utils.logging_utils import get_logger
from nbm_analysis.utils.file_processor import FileProcessor
from nbm_analysis.utils.dataset_logger import DatasetLogger

# Use mock client for local development
if os.getenv('FLASK_ENV') == 'development' or not os.getenv('DATAIKU_LLM_ID'):
    from nbm_analysis.utils.llm_client_mock import SalesAnalysisLLM
    logger = get_logger(__name__)
    logger.info("Using MOCK LLM client for local development")
else:
    from nbm_analysis.utils.llm_client import SalesAnalysisLLM

analysis_blueprint = Blueprint("analysis", __name__, url_prefix="/analysis")
logger = get_logger(__name__)

# Initialize dataset logger
dataset_logger = DatasetLogger(os.getenv('RESULTS_DATASET'))


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

        # Log to dataset if configured
        dataset_logger.log_analysis(
            transcript_source=file.filename,
            evidence_registry=evidence_data.get("evidence_registry", {}),
            sales_whys=analysis_data.get("sales_whys", {}),
            business_context=analysis_data.get("business_context", {}),
            meddic=analysis_data.get("meddic", {}),
            processing_time_seconds=processing_time,
            is_sample=False,
            llm_id=os.getenv('DATAIKU_LLM_ID')
        )

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

        # Log to dataset if configured
        dataset_logger.log_analysis(
            transcript_source="sample_transcript",
            evidence_registry=evidence_data.get("evidence_registry", {}),
            sales_whys=analysis_data.get("sales_whys", {}),
            business_context=analysis_data.get("business_context", {}),
            meddic=analysis_data.get("meddic", {}),
            processing_time_seconds=processing_time,
            is_sample=True,
            llm_id=os.getenv('DATAIKU_LLM_ID')
        )

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


@analysis_blueprint.route("/analyze-stream", methods=["POST"])
def analyze_transcript_stream() -> Response:
    """API endpoint to analyze uploaded transcript with streaming updates"""

    def generate():
        try:
            # Check if file is present
            if 'file' not in request.files:
                yield f"data: {json.dumps({'stage': 'error', 'error': 'No file provided'})}\n\n"
                return

            file = request.files['file']

            # Validate file
            is_valid, message = FileProcessor.validate_file(file)
            if not is_valid:
                logger.warning(f"File validation failed: {message}")
                yield f"data: {json.dumps({'stage': 'error', 'error': message})}\n\n"
                return

            # Read file content
            content = FileProcessor.read_file_content(file)
            if not content:
                logger.error(f"Could not read file content: {file.filename}")
                yield f"data: {json.dumps({'stage': 'error', 'error': 'Could not read file content'})}\n\n"
                return

            # Stream analysis
            start_time = datetime.now()
            llm_client = SalesAnalysisLLM()

            evidence_data = None
            analysis_data = None

            for update in llm_client.create_analysis_streamed(content):
                # Send update to client
                yield f"data: {json.dumps(update)}\n\n"

                # Store data for logging
                if update.get("stage") == "evidence" and update.get("status") == "complete":
                    evidence_data = update.get("data", {})
                elif update.get("stage") == "analysis" and update.get("status") == "complete":
                    analysis_data = update.get("data", {})

            # Log to dataset if we got complete data
            if evidence_data and analysis_data:
                processing_time = (datetime.now() - start_time).total_seconds()
                dataset_logger.log_analysis(
                    transcript_source=file.filename,
                    evidence_registry=evidence_data.get("evidence_registry", {}),
                    sales_whys=analysis_data.get("sales_whys", {}),
                    business_context=analysis_data.get("business_context", {}),
                    meddic=analysis_data.get("meddic", {}),
                    processing_time_seconds=processing_time,
                    is_sample=False,
                    llm_id=os.getenv('DATAIKU_LLM_ID')
                )

        except Exception as e:
            logger.error(f"Unexpected error in streaming analysis: {str(e)}")
            yield f"data: {json.dumps({'stage': 'error', 'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@analysis_blueprint.route("/analyze-sample-stream", methods=["POST"])
def analyze_sample_stream() -> Response:
    """API endpoint to analyze sample transcript with streaming updates"""

    def generate():
        try:
            # Load sample transcript
            content = FileProcessor.load_sample_transcript()
            if not content:
                logger.error("Could not load sample transcript")
                yield f"data: {json.dumps({'stage': 'error', 'error': 'Sample transcript not available'})}\n\n"
                return

            # Stream analysis
            start_time = datetime.now()
            llm_client = SalesAnalysisLLM()

            evidence_data = None
            analysis_data = None

            for update in llm_client.create_analysis_streamed(content, user_email="sample_user"):
                # Send update to client
                yield f"data: {json.dumps(update)}\n\n"

                # Store data for logging
                if update.get("stage") == "evidence" and update.get("status") == "complete":
                    evidence_data = update.get("data", {})
                elif update.get("stage") == "analysis" and update.get("status") == "complete":
                    analysis_data = update.get("data", {})

            # Log to dataset if we got complete data
            if evidence_data and analysis_data:
                processing_time = (datetime.now() - start_time).total_seconds()
                dataset_logger.log_analysis(
                    transcript_source="sample_transcript",
                    evidence_registry=evidence_data.get("evidence_registry", {}),
                    sales_whys=analysis_data.get("sales_whys", {}),
                    business_context=analysis_data.get("business_context", {}),
                    meddic=analysis_data.get("meddic", {}),
                    processing_time_seconds=processing_time,
                    is_sample=True,
                    llm_id=os.getenv('DATAIKU_LLM_ID')
                )

        except Exception as e:
            logger.error(f"Unexpected error in sample streaming analysis: {str(e)}")
            yield f"data: {json.dumps({'stage': 'error', 'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')
