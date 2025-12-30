from flask import Flask
import os, sys
from dotenv import load_dotenv

load_dotenv()

def update_path_for_local_testing():
    cwd = os.getcwd()
    dirnames = cwd.split("/")
    for i in reversed(range(len(dirnames))):
        if dirnames[i] == "python-lib":
            python_path = "/".join(dirnames[: i + 1])
            sys.path.append(python_path)


update_path_for_local_testing()
from nbm_analysis.app_setup import create_app
from nbm_analysis.utils.logging_utils import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":

    app = Flask(__name__)

    local_debug_dir = os.path.join(os.getcwd().split("python-lib")[0], "local-debug")
    local_data_dir = os.path.join(local_debug_dir, "data")

    app.config.update(
        LOCAL_DEBUG_DIR=local_debug_dir,
        LOCAL_DATA_DIR=local_data_dir,
    )

    create_app(app).run(host="0.0.0.0", port=5000, debug=True)
