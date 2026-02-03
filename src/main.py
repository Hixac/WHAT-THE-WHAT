import structlog

from src.core import logger
from src.poster import posting


LOGGER = structlog.get_logger(__name__)


def main():
    LOGGER.info("APPLICATION STARTED")
    posting()


if __name__ == "__main__":
    main()
