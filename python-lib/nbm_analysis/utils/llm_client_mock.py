"""Mock LLM client for local testing without Dataiku"""
import json
import os
from typing import Dict, Any, Generator
from collections import OrderedDict
from nbm_analysis.utils.logging_utils import get_logger
from nbm_analysis.utils.json_utils import clean_json_response

logger = get_logger(__name__)


class SalesAnalysisLLM:
    """Mock LLM client for local testing - returns dummy data"""

    def __init__(self, llm_id: str = None):
        """Initialize mock LLM client"""
        self.llm_id = llm_id or os.getenv('DATAIKU_LLM_ID', 'mock-llm')
        logger.info(f"Mock LLM client initialized with ID: {self.llm_id}")

    def create_analysis_streamed(self, transcript: str, user_email: str = None) -> Generator[Dict[str, Any], None, None]:
        """Stream the complete analysis (mock version)

        Args:
            transcript: The call transcript text
            user_email: Optional user email for logging

        Yields:
            Dictionary updates with stage, data, and optional error
        """
        try:
            logger.info(f"Mock: Starting streamed analysis for user: {user_email}")

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
            yield {
                "stage": "evidence",
                "data": evidence_result,
                "status": "complete",
                "complete": False
            }

            # Stage 2: Analysis
            yield {"stage": "analysis", "status": "started", "complete": False}

            analysis_result = self.create_analysis(evidence_result, user_email)
            yield {
                "stage": "analysis",
                "data": analysis_result,
                "status": "complete",
                "complete": True
            }

        except Exception as e:
            logger.error(f"Mock streaming analysis failed: {str(e)}")
            yield {"stage": "error", "error": str(e), "complete": True}

    def create_evidence_registry(self, transcript: str, user_email: str = None) -> Dict[str, Any]:
        """Return mock evidence registry"""
        logger.info(f"Mock: Creating evidence registry for user: {user_email}")

        return {
            "evidence_registry": {
                "E001": {
                    "quote": "We need to reduce our pricing cycle from 3 weeks to 3 days",
                    "type": "quantitative_data",
                    "context": "CEO mentioned during strategic planning discussion",
                    "relevance": "Clear business objective with measurable timeline"
                },
                "E002": {
                    "quote": "Current manual pricing process involves 12 different people",
                    "type": "process_detail",
                    "context": "Operations manager describing current workflow",
                    "relevance": "Indicates complexity and potential for automation"
                },
                "E003": {
                    "quote": "CFO approved $500K budget for pricing transformation",
                    "type": "quantitative_data",
                    "context": "Budget discussion",
                    "relevance": "Shows executive sponsorship and available funding"
                }
            }
        }

    def create_analysis(self, evidence_registry: Dict[str, Any], user_email: str = None) -> Dict[str, Any]:
        """Return mock analysis"""
        logger.info(f"Mock: Creating analysis for user: {user_email}")

        analysis_data = {
            "three_whys": OrderedDict([
                ("corporate_objectives", {
                    "summary": "Company aims to reduce pricing cycle time by 90% to improve competitiveness and win more deals. CEO and CFO have allocated $500K budget for pricing transformation initiative.",
                    "evidence_ids": ["E001", "E003"]
                }),
                ("domain_initiatives", {
                    "summary": "Operations team is launching a pricing automation project with dedicated resources and Q2 deadline. IT team is evaluating vendor solutions.",
                    "evidence_ids": ["E002"]
                }),
                ("domain_challenges", {
                    "summary": "Current manual process is slow, error-prone, and involves too many stakeholders. Lack of real-time data access and no integration with CRM system.",
                    "evidence_ids": ["E002"]
                })
            ]),
            "meddic": {
                "metrics": {
                    "summary": "Success measured by: 1) Pricing cycle time reduction from 3 weeks to 3 days, 2) Error rate reduction, 3) Deal close rate improvement",
                    "evidence_ids": ["E001"]
                },
                "economic_buyer": {
                    "summary": "CFO is the economic buyer with $500K approved budget. CEO is also engaged and championing the initiative.",
                    "evidence_ids": ["E003"]
                },
                "decision_process": {
                    "summary": "Vendor evaluation in progress. Decision committee includes CFO, COO, and Head of Sales. Target decision date: end of Q1.",
                    "evidence_ids": []
                },
                "decision_criteria": {
                    "summary": "Key criteria: 1) Speed of implementation, 2) Integration with existing CRM, 3) Ease of use, 4) Vendor support and training",
                    "evidence_ids": []
                },
                "implicated_pain": {
                    "summary": "Losing deals to faster competitors due to slow pricing turnaround. Sales team frustrated with manual process and errors.",
                    "evidence_ids": ["E001", "E002"]
                },
                "champion": {
                    "summary": "Head of Sales is advocating for solution. Has strong relationship with CEO and demonstrated pain points.",
                    "evidence_ids": []
                }
            }
        }

        return analysis_data

    def create_deal_review(self, evidence_registry: Dict[str, Any], analysis_data: Dict[str, Any], user_email: str = None) -> Dict[str, Any]:
        """Return mock deal review"""
        logger.info(f"Mock: Creating deal review for user: {user_email}")

        return {
            "deal_review": {
                "stage_readiness": "More Discovery Needed",
                "confidence_note": "While there's clear pain and budget, we're missing key MEDDIC elements like confirmed decision process, timeline, and champion strength. Need more discovery before demo.",
                "critical_gaps": [
                    "No clear timeline for decision - only 'end of Q1' mentioned, need specific date and milestones",
                    "Champion relationship unclear - need to validate Head of Sales has real influence and will advocate during decision",
                    "Competition unknown - are other vendors being evaluated? What's our differentiation?"
                ],
                "next_call_objectives": [
                    "What is the exact decision date and what are the milestones leading up to it?",
                    "Who else is being evaluated and what criteria will be used to choose between vendors?",
                    "Can you walk me through the decision process step-by-step? Who has final say?",
                    "What happens if you don't solve this by Q2? What's the business impact?",
                    "Would the Head of Sales be willing to introduce us to the CFO for a technical discussion?"
                ]
            }
        }
