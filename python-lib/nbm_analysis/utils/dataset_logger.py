"""Logger for writing analysis results to Dataiku datasets"""
import dataiku
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from nbm_analysis.utils.logging_utils import get_logger

logger = get_logger(__name__)


class DatasetLogger:
    """Logs analysis results to a Dataiku dataset"""

    def __init__(self, dataset_name: Optional[str] = None):
        """Initialize dataset logger

        Args:
            dataset_name: Name of the dataset to write to (optional)
        """
        self.dataset_name = dataset_name
        self.enabled = dataset_name is not None and len(dataset_name.strip()) > 0

        if self.enabled:
            logger.info(f"Dataset logging enabled: {dataset_name}")
        else:
            logger.info("Dataset logging disabled (no dataset configured)")

    def log_analysis(
        self,
        transcript_source: str,
        evidence_registry: Dict[str, Any],
        three_whys: Dict[str, Any],
        meddic: Dict[str, Any],
        processing_time_seconds: float,
        is_sample: bool = False,
        deal_review: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        llm_id: Optional[str] = None
    ) -> bool:
        """Log an analysis result to the dataset

        Args:
            transcript_source: Source of transcript (filename or "sample")
            evidence_registry: The evidence registry dict
            three_whys: The three whys analysis dict
            meddic: The MEDDIC analysis dict
            processing_time_seconds: Time taken to analyze
            is_sample: Whether this was the sample transcript
            deal_review: Optional deal review dict
            user_id: Optional user ID
            llm_id: Optional LLM ID used

        Returns:
            True if logged successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Calculate metrics
            num_evidence = len(evidence_registry.get("evidence_registry", {}))

            # Check MEDDIC completeness (has summary that's not "No evidence found")
            meddic_fields_complete = sum([
                1 for field in meddic.values()
                if field.get("summary", "").lower() != "no evidence found" and len(field.get("summary", "")) > 0
            ])

            # Check Three Whys completeness
            three_whys_fields_complete = sum([
                1 for field in three_whys.values()
                if field.get("summary", "").lower() != "no evidence found" and len(field.get("summary", "")) > 0
            ])

            # Create row
            row = {
                "timestamp": datetime.now(),
                "transcript_source": transcript_source,
                "is_sample": is_sample,
                "user_id": user_id or "unknown",
                "llm_id": llm_id or "unknown",
                "processing_time_seconds": processing_time_seconds,
                "num_evidence_items": num_evidence,
                "three_whys_completeness": three_whys_fields_complete,
                "meddic_completeness": meddic_fields_complete,
                "corporate_objectives_summary": three_whys.get("corporate_objectives", {}).get("summary", ""),
                "domain_initiatives_summary": three_whys.get("domain_initiatives", {}).get("summary", ""),
                "domain_challenges_summary": three_whys.get("domain_challenges", {}).get("summary", ""),
                "meddic_metrics_summary": meddic.get("metrics", {}).get("summary", ""),
                "meddic_economic_buyer_summary": meddic.get("economic_buyer", {}).get("summary", ""),
                "meddic_decision_process_summary": meddic.get("decision_process", {}).get("summary", ""),
                "meddic_decision_criteria_summary": meddic.get("decision_criteria", {}).get("summary", ""),
                "meddic_implicated_pain_summary": meddic.get("implicated_pain", {}).get("summary", ""),
                "meddic_champion_summary": meddic.get("champion", {}).get("summary", ""),
                "has_deal_review": deal_review is not None,
                "deal_review_stage_readiness": deal_review.get("stage_readiness", "") if deal_review else "",
                "deal_review_confidence_note": deal_review.get("confidence_note", "") if deal_review else "",
            }

            # Write to dataset
            dataset = dataiku.Dataset(self.dataset_name)

            # Try to append; if dataset doesn't exist, create it
            try:
                df_existing = dataset.get_dataframe()
                df_new = pd.DataFrame([row])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                dataset.write_with_schema(df_combined)
            except Exception as e:
                # Dataset might not exist yet, create it
                logger.info(f"Creating new dataset {self.dataset_name}: {str(e)}")
                df_new = pd.DataFrame([row])
                dataset.write_with_schema(df_new)

            logger.info(f"Logged analysis to dataset {self.dataset_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to log analysis to dataset: {str(e)}")
            return False
