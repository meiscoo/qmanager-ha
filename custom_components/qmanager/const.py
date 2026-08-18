"""Constants for the QManager integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "qmanager"

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)
MIN_SCAN_INTERVAL = 10

CONF_SCAN_INTERVAL_SECONDS = "scan_interval"

# All QManager CGI endpoints live under this prefix.
API_PREFIX = "/cgi-bin/quecmanager"

ENDPOINT_AUTH_CHECK = f"{API_PREFIX}/auth/check.sh"
ENDPOINT_LOGIN = f"{API_PREFIX}/auth/login.sh"
ENDPOINT_LOGOUT = f"{API_PREFIX}/auth/logout.sh"
ENDPOINT_FETCH_DATA = f"{API_PREFIX}/at_cmd/fetch_data.sh"
ENDPOINT_SEND_COMMAND = f"{API_PREFIX}/at_cmd/send_command.sh"
ENDPOINT_CELL_SCAN_START = f"{API_PREFIX}/at_cmd/cell_scan_start.sh"
ENDPOINT_CELL_SCAN_STATUS = f"{API_PREFIX}/at_cmd/cell_scan_status.sh"

SESSION_COOKIE_NAME = "qm_session"

SERVICE_SEND_AT_COMMAND = "send_at_command"
SERVICE_START_CELL_SCAN = "start_cell_scan"

ATTR_COMMAND = "command"
