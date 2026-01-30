import logging
from logging_loki import Lokihandler

# Configure the Loki handler
handler = Lokihandler(
    url="http://localhost:3100/loki/api/v1/push", # Replace with your Loki endpoint
    tags={"application": "my-python-app"},
    version="1",
)

# Get the logger and add the handler
logger = logging.getLogger("my-app")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Log messages
logger.info("This is an informational message", extra={"user": "admin"})
logger.warning("This is a warning message")
