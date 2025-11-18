import yaml
import os
import sys
import json
from loguru import logger
from dotenv import load_dotenv
from .proxy import apply_proxy

# Debug: Print content of .env file before loading
try:
    with open(".env") as f:
        logger.debug(f".env file content:\n{f.read()}")
except FileNotFoundError:
    logger.debug(".env file not found.")

load_dotenv(override=True)

# Get the application environment, default to 'dev' if not set
app_env = os.getenv("APP_ENVIRONMENT", "dev")
logger.info(f"Application Environment (APP_ENVIRONMENT) is set to: '{app_env}'")

# append project path to sys.path
script_path = os.path.abspath(__file__)
project_path = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))

print("project_path is {}".format(project_path))

# append project path to sys.path
sys.path.append(project_path)

# Remove default logger and add a new one based on environment
logger.remove()

if app_env != "local":
    # For GCP, we need a custom formatter to create a JSON payload
    # that GCP Logging can parse correctly, including the severity.
    def gcp_formatter(record):
        log_entry = {
            "severity": record["level"].name,
            "message": record["message"],
            "timestamp": record["time"].isoformat(),
            "logging.googleapis.com/sourceLocation": {
                "file": record["file"].path,
                "line": record["line"],
                "function": record["function"],
            },
        }
        # The sink's format must only contain {message} to output the raw JSON string
        record["extra"]["json_message"] = json.dumps(log_entry)
        return "{extra[json_message]}\n"

    logger.add(sys.stdout, format=gcp_formatter, level="DEBUG")
    logger.info("Loguru configured for custom JSON output to stdout for GCP.")
else:
    # For local development, use standard colorized logging
    logger.add(sys.stderr, level="DEBUG")
    logger.info("Loguru configured for standard terminal output.")



yaml_configs = None
# Dynamically load config file based on the environment
config_file_name = f"config_{app_env}.yaml"
config_file_path = os.path.join(project_path, "src", "configs", config_file_name)

logger.info(f"Attempting to load configuration from: {config_file_path}")

try:
    with open(config_file_path) as f:
        yaml_configs = yaml.load(f, Loader=yaml.FullLoader)
    logger.info(f"Successfully loaded configuration from {config_file_name}")
except FileNotFoundError:
    logger.error(f"Configuration file '{config_file_name}' not found. Please ensure it exists.")
    # Exit or handle the error appropriately
    sys.exit(1)

logger.info("all configs loaded")

if yaml_configs and "proxy" in yaml_configs:
    proxy_settings = yaml_configs["proxy"]
    apply_proxy(
        http_proxy=proxy_settings.get("http"),
        https_proxy=proxy_settings.get("https")
    )
