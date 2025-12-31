import dataiku
import json
import os
from typing import Dict, Any, Generator
from collections import OrderedDict
from dataikuapi.dss.llm import DSSLLMStreamedCompletionChunk, DSSLLMStreamedCompletionFooter
from nbm_analysis.utils.logging_utils import get_logger
from nbm_analysis.utils.json_utils import clean_json_response

logger = get_logger(__name__)


class SalesAnalysisLLM:
    """LLM client for sales call analysis using Dataiku LLMs"""

    def __init__(self, llm_id: str = None):
        """Initialize LLM client

        Args:
            llm_id: Dataiku LLM ID (defaults to environment variable)
        """
        self.llm_id = llm_id or os.getenv('DATAIKU_LLM_ID')
        if not self.llm_id:
            raise ValueError("DATAIKU_LLM_ID must be provided or set in environment")

        # Initialize Dataiku client
        try:
            self.client = dataiku.api_client()
            self.project = self.client.get_default_project()
            self.llm = self.project.get_llm(self.llm_id)
            logger.info(f"LLM client initialized with ID: {self.llm_id}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}")
            raise

    def _create_completion(self, prompt: str, max_tokens: int = 8000) -> str:
        """Create LLM completion

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response

        Returns:
            LLM response text

        Raises:
            Exception: If LLM request fails
        """
        try:
            completion = self.llm.new_completion()
            completion.with_message(prompt)

            # Note: Dataiku LLM API may not support max_tokens directly
            # Adjust based on your Dataiku version's API
            resp = completion.execute()
            return resp.text

        except Exception as e:
            logger.error(f"LLM completion failed: {str(e)}")
            raise

    def create_analysis_streamed(self, transcript: str, user_email: str = None) -> Generator[Dict[str, Any], None, None]:
        """Stream the complete analysis (evidence + frameworks) with progress updates

        Args:
            transcript: The call transcript text
            user_email: Optional user email for logging

        Yields:
            Dictionary updates with stage, data, and optional error
            Format: {"stage": "evidence|analysis", "data": {...}, "complete": bool}
        """
        try:
            # Validate transcript
            if len(transcript) > 50000:
                yield {"stage": "error", "error": "Transcript too long", "complete": True}
                return

            if len(transcript.strip()) < 50:
                yield {"stage": "error", "error": "Transcript too short", "complete": True}
                return

            # Stage 1: Evidence Registry
            yield {"stage": "evidence", "status": "started", "complete": False}

            evidence_result = self.create_evidence_registry(transcript, user_email)
            if "error" in evidence_result:
                yield {"stage": "error", "error": evidence_result["error"], "complete": True}
                return

            yield {
                "stage": "evidence",
                "data": evidence_result,
                "status": "complete",
                "complete": False
            }

            # Stage 2: Analysis (Three Whys + MEDDIC)
            yield {"stage": "analysis", "status": "started", "complete": False}

            analysis_result = self.create_analysis(evidence_result, user_email)
            if "error" in analysis_result:
                yield {"stage": "error", "error": analysis_result["error"], "complete": True}
                return

            # Final result
            yield {
                "stage": "analysis",
                "data": analysis_result,
                "status": "complete",
                "complete": True
            }

        except Exception as e:
            logger.error(f"Streaming analysis failed: {str(e)}")
            yield {"stage": "error", "error": str(e), "complete": True}

    def create_evidence_registry(self, transcript: str, user_email: str = None) -> Dict[str, Any]:
        """Create comprehensive evidence registry from transcript

        Args:
            transcript: The call transcript text
            user_email: Optional user email for logging

        Returns:
            Dictionary containing evidence_registry and optional error
        """
        try:
            # Validate transcript length
            if len(transcript) > 50000:  # ~50k characters max
                return {"evidence_registry": {}, "error": "Transcript too long"}

            if len(transcript.strip()) < 50:
                return {"evidence_registry": {}, "error": "Transcript too short"}

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

            response_text = self._create_completion(prompt, max_tokens=8000)
            cleaned_json = clean_json_response(response_text)

            try:
                result = json.loads(cleaned_json)
                logger.info(f"Evidence registry created for user: {user_email}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON. Error: {str(e)}")
                logger.error(f"Problematic JSON (first 500 chars): {cleaned_json[:500]}")
                logger.error(f"Problematic JSON (around error): {cleaned_json[max(0, e.pos-100):e.pos+100]}")
                return {"evidence_registry": {}, "error": "Analysis failed - please try again"}

        except Exception as e:
            logger.error(f"Unexpected error in evidence registry: {str(e)}")
            return {"evidence_registry": {}, "error": f"Analysis failed: {str(e)}"}

    def create_analysis(self, evidence_registry: Dict[str, Any], user_email: str = None) -> Dict[str, Any]:
        """Create 3 Whys and MEDDIC analysis using evidence registry

        Args:
            evidence_registry: The evidence registry dictionary
            user_email: Optional user email for logging

        Returns:
            Dictionary containing three_whys, meddic, and optional error
        """
        try:
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

            response_text = self._create_completion(prompt, max_tokens=4000)
            cleaned_json = clean_json_response(response_text)

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

        except Exception as e:
            logger.error(f"Unexpected error in analysis: {str(e)}")
            return {"three_whys": {}, "meddic": {}, "error": f"Analysis failed: {str(e)}"}

    def create_deal_review(self, evidence_registry: Dict[str, Any], analysis_data: Dict[str, Any], user_email: str = None) -> Dict[str, Any]:
        """Create deal review with stage readiness assessment and next steps

        Args:
            evidence_registry: The evidence registry dictionary
            analysis_data: The analysis data (three_whys + meddic)
            user_email: Optional user email for logging

        Returns:
            Dictionary containing deal_review and optional error
        """
        try:
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

            response_text = self._create_completion(prompt, max_tokens=2000)
            cleaned_json = clean_json_response(response_text)

            try:
                result = json.loads(cleaned_json)
                logger.info(f"Deal review created for user: {user_email}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse deal review JSON. Error: {str(e)}")
                logger.error(f"Problematic JSON (first 500 chars): {cleaned_json[:500]}")
                return {"deal_review": {}, "error": "Deal review failed - please try again"}

        except Exception as e:
            logger.error(f"Unexpected error in deal review: {str(e)}")
            return {"deal_review": {}, "error": f"Deal review failed: {str(e)}"}
