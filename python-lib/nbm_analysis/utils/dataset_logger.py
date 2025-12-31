"""Logger for writing analysis results to Dataiku datasets"""
import dataiku
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from nbm_analysis.utils.logging_utils import get_logger
import os

logger = get_logger(__name__)


class DatasetLogger:
    """Logs analysis results to a Dataiku dataset"""

    def __init__(self, dataset_name: Optional[str] = None):
        """Initialize dataset logger

        Args:
            dataset_name: Name of the dataset to write to (optional)
                         If not provided or empty, will use 'audit_logs' by default
        """
        # Use 'audit_logs' as default if no dataset name provided
        if not dataset_name or len(dataset_name.strip()) == 0:
            self.dataset_name = "audit_logs"
            logger.info("No dataset configured, using default: audit_logs")
        else:
            self.dataset_name = dataset_name
            logger.info(f"Dataset logging enabled: {dataset_name}")

        self.enabled = True
        self.project = None

        # Try to get project handle (will be None in local dev)
        try:
            client = dataiku.api_client()
            self.project = client.get_default_project()
        except Exception as e:
            logger.warning(f"Could not get Dataiku project (probably local dev): {e}")
            self.enabled = False

    def _ensure_dataset_exists(self) -> bool:
        """Check if dataset exists, create it if it doesn't

        Returns:
            True if dataset exists or was created, False on error
        """
        if not self.project:
            return False

        try:
            # Check if dataset exists
            datasets = self.project.list_datasets()
            dataset_exists = any(ds['name'] == self.dataset_name for ds in datasets)

            if not dataset_exists:
                logger.info(f"Dataset {self.dataset_name} does not exist, creating it...")

                # Create a managed filesystem dataset
                builder = self.project.new_managed_dataset(self.dataset_name)
                builder.with_store_into("filesystem_managed")
                dataset = builder.create()

                logger.info(f"Created dataset {self.dataset_name}")
                return True
            else:
                logger.info(f"Dataset {self.dataset_name} already exists")
                return True

        except Exception as e:
            logger.error(f"Error checking/creating dataset: {e}", exc_info=True)
            return False

    def log_analysis(
        self,
        transcript_source: str,
        evidence_registry: Dict[str, Any],
        sales_whys: Dict[str, Any],
        business_context: Dict[str, Any],
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
            sales_whys: The sales whys analysis dict (why_anything, why_now, why_us)
            business_context: The business context dict (corporate_objectives, domain_initiatives, domain_challenges)
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
            logger.info("Dataset logging disabled (not in Dataiku environment)")
            return False

        # Ensure dataset exists before trying to write
        if not self._ensure_dataset_exists():
            logger.error("Could not ensure dataset exists, skipping logging")
            return False

        try:
            logger.info(f"Attempting to log analysis to dataset: {self.dataset_name}")

            # Calculate metrics
            num_evidence = len(evidence_registry.get("evidence_registry", {}))

            # Check MEDDIC completeness (has summary that's not "No evidence found")
            meddic_fields_complete = sum([
                1 for field in meddic.values()
                if field.get("summary", "").lower() != "no evidence found" and len(field.get("summary", "")) > 0
            ])

            # Check Sales Whys completeness
            sales_whys_fields_complete = sum([
                1 for field in sales_whys.values()
                if field.get("summary", "").lower() != "no evidence found" and len(field.get("summary", "")) > 0
            ])

            # Check Business Context completeness
            business_context_fields_complete = sum([
                1 for field in business_context.values()
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
                "sales_whys_completeness": sales_whys_fields_complete,
                "business_context_completeness": business_context_fields_complete,
                "meddic_completeness": meddic_fields_complete,
                "why_anything_summary": sales_whys.get("why_anything", {}).get("summary", ""),
                "why_now_summary": sales_whys.get("why_now", {}).get("summary", ""),
                "why_us_summary": sales_whys.get("why_us", {}).get("summary", ""),
                "corporate_objectives_summary": business_context.get("corporate_objectives", {}).get("summary", ""),
                "domain_initiatives_summary": business_context.get("domain_initiatives", {}).get("summary", ""),
                "domain_challenges_summary": business_context.get("domain_challenges", {}).get("summary", ""),
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

            logger.info(f"Row prepared with {len(row)} fields")

            # Write to dataset
            logger.info(f"Getting dataset handle for: {self.dataset_name}")
            dataset = dataiku.Dataset(self.dataset_name)

            # Create DataFrame
            df_new = pd.DataFrame([row])
            logger.info(f"Created DataFrame with shape: {df_new.shape}")
            logger.info(f"DataFrame columns: {list(df_new.columns)}")
            logger.info(f"DataFrame dtypes: {df_new.dtypes.to_dict()}")

            # Try to read existing data and append, or create new if doesn't exist
            try:
                logger.info("Attempting to read existing dataset to check if it has data...")
                # Use limit=1 to quickly check if dataset has schema
                existing_df = dataset.get_dataframe(limit=1)
                logger.info(f"Dataset exists with schema. Columns: {list(existing_df.columns)}")

                # Dataset exists, append to it
                logger.info("Appending to existing dataset...")
                dataset.write_dataframe(df_new, infer_schema=False)
                logger.info("Successfully appended to existing dataset")

            except Exception as read_err:
                # Dataset doesn't have data yet, write with schema
                logger.info(f"Dataset doesn't have data yet ({str(read_err)}). Writing with schema...")
                dataset.write_with_schema(df_new)
                logger.info("Successfully created dataset with schema")

            logger.info(f"Successfully logged analysis to dataset {self.dataset_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to log analysis to dataset: {str(e)}", exc_info=True)
            return False
