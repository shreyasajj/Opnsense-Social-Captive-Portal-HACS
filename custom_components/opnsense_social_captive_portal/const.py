"""Constants for the Captive Portal integration."""

DOMAIN = "captive_portal"
CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 3000
SCAN_INTERVAL = 10  # seconds

# API Endpoints
API_STATUS = "/api/ha/status"
API_PENDING = "/api/admin/pending"
API_APPROVE = "/api/admin/approve"
API_DENY = "/api/admin/deny"

# Entity IDs
SENSOR_PENDING = "pending_requests"
SENSOR_APPROVED = "approved_users"
SENSOR_DENIED = "denied_users"
SENSOR_TRACKED = "tracked_devices"
