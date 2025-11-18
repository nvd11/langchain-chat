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


def gcp_formatter(record):
    return {
        "severity": record["level"].name,
        "message": record["message"],
        "timestamp": record["time"].isoformat(),
        "file": record["file"].path,
        "line": record["line"],
        "function": record["function"],
    }

# 添加一个新的处理器 (sink)
# 1. sys.stdout: 指定输出目标为标准输出。
# 2. format=gcp_formatter: 使用我们自定义的格式化函数。
# 3. serialize=True: 告诉 loguru 将格式化函数返回的字典序列化为 JSON 字符串。
# 4. level="DEBUG": 设置此处理器的过滤阈值，确保 DEBUG 及以上所有级别的日志都会被处理。
logger.add(sys.stdout, format=gcp_formatter, level="DEBUG", serialize=True)

logger.info("日志系统已配置为输出与 GCP 兼容的 JSON 到 stdout")



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
