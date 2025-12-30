import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import Tuple, Optional
from nbm_analysis.utils.logging_utils import get_logger

# Try to import docx, handle gracefully if not available
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


logger = get_logger(__name__)

# File upload configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'txt', 'docx'}
ALLOWED_MIME_TYPES = {
    'text/plain',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/octet-stream'  # Sometimes docx files are detected as this
}


class FileProcessor:
    """Handles file upload validation and content extraction"""

    @staticmethod
    def validate_file(file: FileStorage) -> Tuple[bool, str]:
        """Validate uploaded file for security and format

        Args:
            file: Uploaded file object

        Returns:
            Tuple of (is_valid, message)
        """
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

    @staticmethod
    def safe_filename(filename: str) -> str:
        """Generate a safe filename

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        return secure_filename(filename)

    @staticmethod
    def read_file_content(file: FileStorage) -> Optional[str]:
        """Read content from uploaded file with validation

        Args:
            file: Uploaded file object

        Returns:
            File content as string, or None if invalid
        """
        try:
            content_type = file.content_type or ''
            filename = file.filename or 'unknown'

            # Validate content type
            if content_type not in ALLOWED_MIME_TYPES:
                logger.warning(f"Suspicious file type: {content_type} for file: {filename}")
                return None

            if content_type == "text/plain":
                file_content = file.read()
                content = file_content.decode("utf-8")
                # Basic content validation
                if len(content.strip()) < 10:
                    logger.warning(f"File too short: {filename}")
                    return None
                return content
            elif DOCX_AVAILABLE and ("wordprocessingml" in content_type or content_type == "application/octet-stream"):
                # Read .docx file
                doc = Document(file)
                content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                if len(content.strip()) < 10:
                    logger.warning(f"DOCX file too short: {filename}")
                    return None
                return content
            else:
                logger.warning(f"Unsupported content type: {content_type}")
                return None

        except UnicodeDecodeError:
            logger.warning(f"Invalid text encoding in file: {file.filename}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file.filename}: {str(e)}")
            return None

    @staticmethod
    def load_sample_transcript() -> Optional[str]:
        """Load sample transcript from file

        Returns:
            Sample transcript content, or None if not found
        """
        try:
            # Try multiple possible locations
            # __file__ points to this utils/file_processor.py
            # So ../../sample_transcript.txt goes up to nbm_analysis/sample_transcript.txt
            possible_paths = [
                # Relative to the utils directory (most reliable in Dataiku)
                os.path.join(os.path.dirname(__file__), '../sample_transcript.txt'),
                # Relative to nbm_analysis directory
                os.path.join(os.path.dirname(__file__), '../../sample_transcript.txt'),
                # In current working directory (local dev)
                'sample_transcript.txt',
                'sales-call-analyzer/sample_transcript.txt',
                os.path.join(os.getcwd(), 'sample_transcript.txt'),
                # Absolute path in Dataiku
                './python-lib/nbm_analysis/sample_transcript.txt'
            ]

            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        logger.info(f"Sample transcript loaded from: {abs_path}")
                        return content

            # Log all attempted paths for debugging
            logger.error("sample_transcript.txt not found in any expected location")
            logger.error(f"Tried paths: {[os.path.abspath(p) for p in possible_paths]}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"__file__ directory: {os.path.dirname(__file__)}")
            return None

        except Exception as e:
            logger.error(f"Error loading sample transcript: {str(e)}")
            return None
