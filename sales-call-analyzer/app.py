from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
import anthropic
import json
import os
from typing import Dict, Any
from google.oauth2 import id_token
from google.auth.transport import requests
import secrets
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import logging
from collections import OrderedDict
import re
import warnings

# Try to import docx, handle gracefully if not available
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Try to import flask-limiter, handle gracefully if not available
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    print("Warning: flask-limiter not installed. Rate limiting disabled.")

app = Flask(__name__)

# Secret key - use env var if available, otherwise generate (non-blocking)
# secrets.token_hex is fast and shouldn't block, but we use env var as primary
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(16)

# Security configuration
app.config.update(
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB max file size
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    SESSION_COOKIE_SECURE=True if os.getenv('FLASK_ENV') == 'production' else False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# File upload configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'txt', 'docx'}
ALLOWED_MIME_TYPES = {
    'text/plain', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/octet-stream'  # Sometimes docx files are detected as this
}

# Setup logging early (non-blocking)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables with validation
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Validate required environment variables (fail fast if missing - better than timeout)
required_vars = {
    'ANTHROPIC_API_KEY': ANTHROPIC_API_KEY,
    'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize rate limiter at import time (before first request)
# Must be done before app handles any requests, otherwise Flask-Limiter fails
# IMPORTANT: Check for RATELIMIT_STORAGE_URL - if set, it will try to connect to Redis/other storage
# which can cause worker timeouts. We force in-memory storage to avoid this.
limiter = None
if LIMITER_AVAILABLE:
    # Check if storage URL is set - if so, warn and disable to prevent timeouts
    storage_url = os.getenv('RATELIMIT_STORAGE_URL') or os.getenv('REDIS_URL')
    if storage_url:
        logger.warning(f"RATELIMIT_STORAGE_URL/REDIS_URL detected: {storage_url[:50]}...")
        logger.warning("Rate limiter will try to connect to external storage, which may cause timeouts.")
        logger.warning("Disabling rate limiter to prevent worker startup timeouts.")
        logger.warning("To enable rate limiting, remove RATELIMIT_STORAGE_URL/REDIS_URL or use in-memory storage.")
        limiter = None
    else:
        try:
            # Suppress the in-memory storage warning (we're intentionally using it)
            warnings.filterwarnings('ignore', message='Using the in-memory storage for tracking rate limits')

            # Initialize with in-memory storage (no network calls)
            limiter = Limiter(
                key_func=get_remote_address,
                app=app,
                default_limits=["200 per day", "50 per hour"]
            )
            logger.info("Rate limiter initialized successfully with in-memory storage")
        except Exception as e:
            logger.warning(f"Failed to initialize rate limiter: {e}. Rate limiting disabled.")
            limiter = None
else:
    logger.info("Rate limiter not available (flask-limiter not installed)")

def validate_file(file):
    """Validate uploaded file for security"""
    if not file or not file.filename:
        return False, "No file selected"
    
    # Check file extension
    if '.' not in file.filename:
        return False, "File must have an extension"
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type .{ext} not allowed. Only .txt and .docx files are supported"
    
    # Check file size (additional check beyond Flask's MAX_CONTENT_LENGTH)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if size == 0:
        return False, "File is empty"
    
    return True, "File is valid"

def safe_filename(filename):
    """Generate a safe filename"""
    return secure_filename(filename)

def load_sample_transcript():
    """Load sample transcript from file"""
    try:
        with open('sample_transcript.txt', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error("sample_transcript.txt not found")
        return None
    except Exception as e:
        logger.error(f"Error loading sample transcript: {str(e)}")
        return None

@app.route('/api/analyze-sample', methods=['POST'])
def analyze_sample():
    """API endpoint to analyze sample transcript"""
    # Apply rate limiting if available
    if limiter:
        try:
            limiter.limit("5 per minute")(lambda: None)()
        except Exception:
            return jsonify({"error": "Too many analysis requests. Please wait before trying again."}), 429
    
    # Check authentication
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    user_email = session['user'].get('email', 'unknown')
    
    if not ANTHROPIC_API_KEY:
        logger.error("Anthropic API key not configured")
        return jsonify({"error": "Analysis service not configured"}), 500
    
    try:
        start_time = datetime.now()
        
        # Load sample transcript
        content = load_sample_transcript()
        if not content:
            logger.error(f"Could not load sample transcript for {user_email}")
            return jsonify({"error": "Sample transcript not available. Please try uploading your own file."}), 400
        
        # Create evidence registry
        evidence_data = create_evidence_registry(content, user_email)
        if "error" in evidence_data:
            logger.error(f"Sample evidence registry failed for {user_email}: {evidence_data['error']}")
            return jsonify({"error": f"Sample analysis failed: {evidence_data['error']}"}), 500
        
        # Create analysis
        analysis_data = create_analysis(evidence_data, user_email)
        if "error" in analysis_data:
            logger.error(f"Sample analysis failed for {user_email}: {analysis_data['error']}")
            return jsonify({"error": f"Sample analysis failed: {analysis_data['error']}"}), 500
        
        # Log successful analysis
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Sample analysis completed for {user_email} in {processing_time:.2f}s")
        
        # Combine results and add sample indicator
        result = {**evidence_data, **analysis_data, "is_sample": True}
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Unexpected error in sample analysis for {user_email}: {str(e)}")
        return jsonify({"error": "Sample analysis failed due to an unexpected error. Please try again."}), 500

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Error handlers
@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({"error": "File too large. Maximum size is 5MB"}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "Page not found"}), 404

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unexpected errors"""
    # Don't catch 404s here - let them be handled by the 404 handler
    if hasattr(e, 'code') and e.code == 404:
        return not_found(e)
    
    logger.error(f"Unexpected error: {str(e)}")
    return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

# Initialize Google Sheets client
def get_sheets_client():
    """Initialize Google Sheets client"""
    try:
        if not GOOGLE_SHEETS_CREDENTIALS:
            return None
        
        # Parse credentials from environment variable
        creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        print(f"Failed to initialize Google Sheets client: {e}")
        return None

def add_email_to_sheet(email, name=None):
    """Add email to Google Sheets"""
    try:
        client = get_sheets_client()
        if not client or not GOOGLE_SHEET_ID:
            print("Google Sheets not configured")
            return False
        
        # Open the spreadsheet
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        
        # Add headers if sheet is empty
        if not sheet.get_all_values():
            sheet.append_row(['Email', 'Name', 'Timestamp', 'Status'])
        
        # Add the email
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sheet.append_row([email, name or '', timestamp, 'Signed Up'])
        
        print(f"Added email to sheet: {email}")
        return True
        
    except Exception as e:
        print(f"Failed to add email to sheet: {e}")
        return False

def read_file_content(file_content, content_type, filename):
    """Read content from uploaded file with validation"""
    try:
        # Validate content type
        if content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"Suspicious file type: {content_type} for file: {filename}")
            return None
        
        if content_type == "text/plain":
            content = file_content.decode("utf-8")
            # Basic content validation
            if len(content.strip()) < 10:
                logger.warning(f"File too short: {filename}")
                return None
            return content
        elif DOCX_AVAILABLE and ("wordprocessingml" in content_type or content_type == "application/octet-stream"):
            # For MVP, return placeholder - proper docx handling would require temporary file
            return "Word document support needs implementation"
        else:
            return None
    except UnicodeDecodeError:
        logger.warning(f"Invalid text encoding in file: {filename}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {filename}: {str(e)}")
        return None

def clean_json_response(text: str) -> str:
    """Clean and extract JSON from AI response"""
    # Remove markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # Try to find JSON object directly
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

    # Remove trailing commas before closing braces/brackets
    text = re.sub(r',(\s*[}\]])', r'\1', text)

    return text.strip()

def create_evidence_registry(transcript: str, user_email: str = None) -> Dict[str, Any]:
    """Create comprehensive evidence registry from transcript"""
    try:
        # Validate transcript length
        if len(transcript) > 50000:  # ~50k characters max
            return {"evidence_registry": {}, "error": "Transcript too long"}

        if len(transcript.strip()) < 50:
            return {"evidence_registry": {}, "error": "Transcript too short"}

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = """
        You are an expert at extracting and cataloging evidence from sales call transcripts.

        Your task is to create a comprehensive evidence registry that captures ALL relevant information from this transcript.

        Evidence Collection Standards:
        - Direct Quotes: Exact wording from the transcript
        - Implied Information: Clear contextual references and implications
        - Quantitative Data: All numbers, timeframes, frequencies, and metrics mentioned
        - Process Details: Current workflows, pain points, and operational context

        For each piece of evidence, assign a unique ID (E001, E002, etc.) and categorize it.

        Extract every meaningful piece of information - be thorough and comprehensive.

        IMPORTANT: Return ONLY valid JSON with no trailing commas. Ensure all quotes are properly escaped.

        Return your response as a JSON object with this structure:
        {
            "evidence_registry": {
                "E001": {
                    "quote": "exact quote from transcript",
                    "type": "direct_quote|implied_info|quantitative_data|process_detail",
                    "context": "brief context about when/why this was mentioned",
                    "relevance": "why this evidence is important for sales analysis"
                }
            }
        }

        Transcript:
        """ + transcript

        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=8000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON from text response
        text_content = response.content[0].text
        cleaned_json = clean_json_response(text_content)

        try:
            result = json.loads(cleaned_json)
            logger.info(f"Evidence registry created for user: {user_email}")
            return result
        except json.JSONDecodeError as e:
            # Log the problematic JSON for debugging
            logger.error(f"Failed to parse JSON. Error: {str(e)}")
            logger.error(f"Problematic JSON (first 500 chars): {cleaned_json[:500]}")
            logger.error(f"Problematic JSON (around error): {cleaned_json[max(0, e.pos-100):e.pos+100]}")
            return {"evidence_registry": {}, "error": "Analysis failed - please try again"}

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {str(e)}")
        return {"evidence_registry": {}, "error": "AI analysis service temporarily unavailable"}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {str(e)}")
        return {"evidence_registry": {}, "error": "Analysis failed - please try again"}
    except Exception as e:
        logger.error(f"Unexpected error in evidence registry: {str(e)}")
        return {"evidence_registry": {}, "error": "Analysis failed - please try again"}

def create_analysis(evidence_registry: Dict[str, Any], user_email: str = None) -> Dict[str, Any]:
    """Create 3 Whys and MEDDIC analysis using evidence registry"""
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = """
        You are a sales expert analyzing a call transcript. Use ONLY the evidence provided in the evidence registry to create your analysis.

        Evidence Registry:
        """ + json.dumps(evidence_registry, indent=2) + """

        Create a comprehensive analysis with two frameworks:

        1. Three Whys Framework (HIERARCHICAL - from strategic to operational):

        - Corporate Objectives: C-level strategic goals with executive sponsorship and significant budget (revenue targets, market expansion, compliance mandates). Look for: "CEO wants", "board approved", "company goal", numbers/percentages, annual targets. ONLY use quantitative_data and executive-level direct_quotes evidence.

        - Domain Initiatives: Department-level projects that support objectives with dedicated teams and timelines. Look for: "we're launching", "team is working on", project names, specific deadlines, allocated resources. ONLY use process_detail and project-related direct_quotes evidence.

        - Domain Challenges: Day-to-day operational challenges blocking progress that we can solve. Look for: "struggling with", "takes too long", "can't integrate", "manual process", current state problems. ONLY use process_detail and operational implied_info evidence.

        2. MEDDIC Framework:
        - Metrics: What measurable criteria matter to them?
        - Economic Buyer: Who has budget authority?
        - Decision Process: How do they make decisions?
        - Decision Criteria: What factors influence their choices?
        - Implicated Pain: What pain points need solving?
        - Champion: Who supports/advocates for solutions?

        For each analysis point:
        - Provide a clear summary
        - Reference specific evidence IDs that support your analysis
        - Use evidence that matches the appropriate scope/level for each section
        - If no evidence exists for a section, state "No evidence found"

        IMPORTANT: Return the three_whys object with keys in this EXACT order:
        1. corporate_objectives (first)
        2. domain_initiatives (second)
        3. domain_challenges (third)

        Return as JSON:
        {
            "three_whys": {
                "corporate_objectives": {
                    "summary": "analysis summary",
                    "evidence_ids": ["E001", "E002"]
                },
                "domain_initiatives": {
                    "summary": "analysis summary",
                    "evidence_ids": ["E003"]
                },
                "domain_challenges": {
                    "summary": "analysis summary",
                    "evidence_ids": ["E004", "E005"]
                }
            },
            "meddic": {
                "metrics": {"summary": "analysis summary", "evidence_ids": ["E006"]},
                "economic_buyer": {"summary": "analysis summary", "evidence_ids": ["E007"]},
                "decision_process": {"summary": "analysis summary", "evidence_ids": ["E008"]},
                "decision_criteria": {"summary": "analysis summary", "evidence_ids": ["E009"]},
                "implicated_pain": {"summary": "analysis summary", "evidence_ids": ["E010"]},
                "champion": {"summary": "analysis summary", "evidence_ids": ["E011"]}
            }
        }
        """
        
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=4000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON from text response
        text_content = response.content[0].text
        cleaned_json = clean_json_response(text_content)

        try:
            analysis_data = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis JSON. Error: {str(e)}")
            logger.error(f"Problematic JSON (first 500 chars): {cleaned_json[:500]}")
            return {"three_whys": {}, "meddic": {}, "error": "Analysis failed - please try again"}

        # Ensure three_whys is properly ordered using OrderedDict
        if 'three_whys' in analysis_data:
            ordered_three_whys = OrderedDict()
            ordered_three_whys['corporate_objectives'] = analysis_data['three_whys'].get('corporate_objectives', {})
            ordered_three_whys['domain_initiatives'] = analysis_data['three_whys'].get('domain_initiatives', {})
            ordered_three_whys['domain_challenges'] = analysis_data['three_whys'].get('domain_challenges', {})
            analysis_data['three_whys'] = ordered_three_whys

        logger.info(f"Analysis created for user: {user_email}")
        return analysis_data

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error in analysis: {str(e)}")
        return {"three_whys": {}, "meddic": {}, "error": "AI analysis service temporarily unavailable"}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse analysis response as JSON: {str(e)}")
        return {"three_whys": {}, "meddic": {}, "error": "Analysis failed - please try again"}
    except Exception as e:
        logger.error(f"Unexpected error in analysis: {str(e)}")
        return {"three_whys": {}, "meddic": {}, "error": "Analysis failed - please try again"}

def create_deal_review(evidence_registry: Dict[str, Any], analysis_data: Dict[str, Any], user_email: str = None) -> Dict[str, Any]:
    """Create deal review with stage readiness assessment and next steps"""
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = """
        You are a tough but fair sales manager reviewing this deal. Based on the evidence and analysis provided, give me an honest assessment.

        Evidence Registry:
        """ + json.dumps(evidence_registry, indent=2) + """

        Analysis Data:
        """ + json.dumps(analysis_data, indent=2) + """

        Provide a direct, no-nonsense deal review focusing on:

        1. STAGE READINESS: Determine if this deal needs "More Discovery Needed" or "Ready for Demo"
        - Look for concrete evidence of pain, budget, authority, timeline
        - If missing >2 critical MEDDIC elements, it's "More Discovery Needed"
        - Be honest about deal strength

        2. CRITICAL GAPS: Identify the 2-3 most important missing pieces that could kill this deal
        - Focus on deal-breakers, not nice-to-haves
        - Be specific about what's missing
        - Call out assumptions vs confirmed facts

        3. NEXT CALL OBJECTIVES: Provide 3-5 specific, actionable questions to ask in the next conversation
        - Make them copy-pasteable
        - Focus on filling the critical gaps
        - Include discovery questions about decision process, stakeholders, budget

        Be direct and honest - sugar-coating helps no one. This rep needs to know the truth about their deal.

        Return as JSON:
        {
            "deal_review": {
                "stage_readiness": "More Discovery Needed" or "Ready for Demo",
                "confidence_note": "brief explanation of why",
                "critical_gaps": [
                    "specific gap 1",
                    "specific gap 2",
                    "specific gap 3"
                ],
                "next_call_objectives": [
                    "specific question 1",
                    "specific question 2",
                    "specific question 3",
                    "specific question 4",
                    "specific question 5"
                ]
            }
        }
        """
        
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON from text response
        text_content = response.content[0].text
        cleaned_json = clean_json_response(text_content)

        try:
            result = json.loads(cleaned_json)
            logger.info(f"Deal review created for user: {user_email}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse deal review JSON. Error: {str(e)}")
            logger.error(f"Problematic JSON (first 500 chars): {cleaned_json[:500]}")
            return {"deal_review": {}, "error": "Deal review failed - please try again"}

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error in deal review: {str(e)}")
        return {"deal_review": {}, "error": "Deal review service temporarily unavailable"}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse deal review response as JSON: {str(e)}")
        return {"deal_review": {}, "error": "Deal review failed - please try again"}
    except Exception as e:
        logger.error(f"Unexpected error in deal review: {str(e)}")
        return {"deal_review": {}, "error": "Deal review failed - please try again"}


@app.route('/api/deal-review', methods=['POST'])
def create_deal_review_endpoint():
    """API endpoint to create deal review from existing analysis"""
    # Apply rate limiting if available
    if limiter:
        try:
            limiter.limit("10 per minute")(lambda: None)()
        except Exception:
            return jsonify({"error": "Too many requests. Please wait before trying again."}), 429
    
    # Check authentication
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    user_email = session['user'].get('email', 'unknown')
    
    if not ANTHROPIC_API_KEY:
        logger.error("Anthropic API key not configured")
        return jsonify({"error": "Deal review service not configured"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        evidence_registry = data.get('evidence_registry', {})
        analysis_data = data.get('analysis_data', {})
        
        if not evidence_registry or not analysis_data:
            return jsonify({"error": "Missing analysis data for deal review"}), 400
        
        # Create deal review
        deal_review_data = create_deal_review(evidence_registry, analysis_data, user_email)
        
        if "error" in deal_review_data:
            logger.error(f"Deal review failed for {user_email}: {deal_review_data['error']}")
            return jsonify({"error": f"Deal review failed: {deal_review_data['error']}"}), 500
        
        logger.info(f"Deal review completed for {user_email}")
        return jsonify(deal_review_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in deal review endpoint for {user_email}: {str(e)}")
        return jsonify({"error": "Deal review failed due to an unexpected error. Please try again."}), 500
@app.route('/api/config')
def get_config():
    """Get client-side configuration"""
    return jsonify({
        "google_client_id": GOOGLE_CLIENT_ID
    })

@app.route('/api/signup', methods=['POST'])
def signup():
    """Capture email for signup"""
    # Apply rate limiting if available
    if limiter:
        try:
            limiter.limit("10 per minute")(lambda: None)()
        except Exception:
            return jsonify({"error": "Too many signup attempts. Please try again later."}), 429
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email or len(email) < 5:
            return jsonify({"error": "Invalid email format"}), 400
        
        # Check email length
        if len(email) > 254:
            return jsonify({"error": "Email too long"}), 400
        
        # Add to Google Sheets
        success = add_email_to_sheet(email)
        
        if success:
            # Store email in session for later use
            session['signup_email'] = email
            logger.info(f"Email captured: {email}")
            return jsonify({"success": True, "message": "Email captured successfully"})
        else:
            return jsonify({"error": "Failed to save email. Please try again."}), 500
            
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({"error": "Signup failed. Please try again."}), 500

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Verify Google OAuth token"""
    try:
        token = request.json.get('token')
        if not token:
            return jsonify({"error": "No token provided"}), 400
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return jsonify({"error": "Invalid token issuer"}), 400
        
        # Store user info in session
        session['user'] = {
            'email': idinfo['email'],
            'name': idinfo['name'],
            'picture': idinfo.get('picture', ''),
            'google_id': idinfo['sub']
        }
        
        # If we have a signup email, update the sheet with the name
        if 'signup_email' in session:
            signup_email = session['signup_email']
            if signup_email == idinfo['email']:
                # Update the sheet with the name
                try:
                    client = get_sheets_client()
                    if client and GOOGLE_SHEET_ID:
                        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
                        # Find the row with this email and update the name
                        all_records = sheet.get_all_records()
                        for i, record in enumerate(all_records):
                            if record.get('Email') == signup_email and not record.get('Name'):
                                sheet.update_cell(i + 2, 2, idinfo['name'])  # +2 because of header row and 0-indexing
                                break
                except Exception as e:
                    print(f"Failed to update name in sheet: {e}")
            
            # Clear the signup email from session
            session.pop('signup_email', None)
        
        return jsonify({
            "success": True,
            "user": session['user']
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid token: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({"success": True})

@app.route('/api/auth/status')
def auth_status():
    """Check if user is authenticated"""
    if 'user' in session:
        return jsonify({
            "authenticated": True,
            "user": session['user']
        })
    return jsonify({"authenticated": False})

@app.route('/')
def landing():
    """Serve the landing page"""
    try:
        return send_from_directory('.', 'landing.html')
    except FileNotFoundError:
        logger.error("landing.html not found")
        return jsonify({"error": "Landing page not found"}), 404

@app.route('/app')
def app_page():
    """Serve the main application"""
    return send_from_directory('.', 'index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint to analyze uploaded transcript"""
    # Apply rate limiting if available
    if limiter:
        try:
            limiter.limit("5 per minute")(lambda: None)()
        except Exception:
            return jsonify({"error": "Too many analysis requests. Please wait before trying again."}), 429
    
    # Check authentication
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    user_email = session['user'].get('email', 'unknown')
    
    if not ANTHROPIC_API_KEY:
        logger.error("Anthropic API key not configured")
        return jsonify({"error": "Analysis service not configured"}), 500
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    # Validate file
    is_valid, error_message = validate_file(file)
    if not is_valid:
        logger.warning(f"Invalid file upload from {user_email}: {error_message}")
        return jsonify({"error": error_message}), 400
    
    # Generate safe filename
    safe_name = safe_filename(file.filename)
    
    try:
        start_time = datetime.now()
        
        # Read file content with validation
        file_content = file.read()
        content = read_file_content(file_content, file.content_type, safe_name)
        
        if not content:
            logger.warning(f"Could not read file content from {user_email}: {safe_name}")
            return jsonify({"error": "Could not read file content. Please ensure it's a valid text file."}), 400
        
        # Create evidence registry
        evidence_data = create_evidence_registry(content, user_email)
        if "error" in evidence_data:
            logger.error(f"Evidence registry failed for {user_email}: {evidence_data['error']}")
            return jsonify({"error": f"Analysis failed: {evidence_data['error']}"}), 500
        
        # Create analysis
        analysis_data = create_analysis(evidence_data, user_email)
        if "error" in analysis_data:
            logger.error(f"Analysis failed for {user_email}: {analysis_data['error']}")
            return jsonify({"error": f"Analysis failed: {analysis_data['error']}"}), 500
        
        # Log successful analysis
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Analysis completed for {user_email} in {processing_time:.2f}s")
        
        # Combine results
        result = {**evidence_data, **analysis_data}
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Unexpected error in analysis for {user_email}: {str(e)}")
        return jsonify({"error": "Analysis failed due to an unexpected error. Please try again."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5500))
    app.run(host='0.0.0.0', port=port, debug=True)