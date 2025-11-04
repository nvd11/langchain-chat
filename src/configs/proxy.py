import os
from loguru import logger

def apply_proxy(http_proxy=None, https_proxy=None):
    """
    Applies proxy settings to environment variables.
    """
    if http_proxy:
        os.environ["HTTP_PROXY"] = http_proxy
        logger.info(f"HTTP_PROXY set to: {http_proxy}")
    
    if https_proxy:
        os.environ["HTTPS_PROXY"] = https_proxy
        logger.info(f"HTTPS_PROXY set to: {https_proxy}")

    if not http_proxy and not https_proxy:
        logger.info("No proxy settings provided to apply.")
