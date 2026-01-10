import logging
from app.core.config import settings

if settings.app_env == "development":
    LOG_LEVEL = logging.DEBUG
elif settings.app_env == "production":
    LOG_LEVEL = logging.INFO



logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(name)s  %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)