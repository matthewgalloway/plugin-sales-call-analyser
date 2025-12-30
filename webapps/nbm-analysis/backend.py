import dataiku
from dataiku.customwebapp import *
from dataiku import SQLExecutor2

from dotenv import load_dotenv
import os

load_dotenv("./python-lib/nbm_analysis/prodenv/.env")

# get log level from input params
log_level = get_webapp_config()["log_level"]
os.environ["FLASK_LOG_LEVEL"] = log_level

# get LLM ID from webapp config
llm_id = get_webapp_config()["llm_id"]
os.environ["DATAIKU_LLM_ID"] = llm_id

# get results dataset from webapp config (optional)
results_dataset = get_webapp_config().get("results_dataset", "")
os.environ["RESULTS_DATASET"] = results_dataset

from nbm_analysis.utils.logging_utils import get_logger
from nbm_analysis.app_setup import create_app

logger = get_logger(__name__)

create_app(app)
