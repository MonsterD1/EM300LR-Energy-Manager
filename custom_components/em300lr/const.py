"""Constants for the B-Control EM300 LR integration."""

from datetime import timedelta

DOMAIN = "em300lr"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 3600

DEFAULT_NAME = "BControlEM300"
MANUFACTURER = "TQ / B-Control"
MODEL = "EM300 LR"

REQUEST_TIMEOUT = timedelta(seconds=10)
