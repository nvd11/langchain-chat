import yaml
import os
import sys
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


# setup logs path
logger.add(os.path.join(project_path, "logs", "app.log"), level="DEBUG")

logger.info("basic setup done")


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

if "deepseek" in yaml_configs and "api-key" in yaml_configs["deepseek"]:
    api_key_env_var = yaml_configs["deepseek"]["api-key"]
    api_key = os.getenv(api_key_env_var)
    if api_key:
        yaml_configs["deepseek"]["api-key"] = api_key
        logger.info(f"Environment variable for DeepSeek found, using the value from environment variable")
    else:
        logger.warning(f"Environment variable {api_key_env_var} not found, using value from config file")
