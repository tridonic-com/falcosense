"""Constants for the FalcoSENSE client."""

from __future__ import annotations

from typing import Final

DEFAULT_HTTPS_PORT: Final = 5000
DEFAULT_MQTT_PORT: Final = 1883
MQTT_WEBSOCKET_PATH: Final = "/ws"

# REST API paths (served under https://<host>:<port>/).
REST_VERSION: Final = "version"
REST_DEVICE_NAME: Final = "tridonic_indoor/get_device_name"
REST_TIMEZONE: Final = "tridonic_indoor/timezone"
REST_RESET_TIME: Final = "tridonic_indoor/resetTime"
REST_AUTHENTICATE_MQTT: Final = "authenticate_mqtt"
REST_LINE_COUNTERS: Final = "tridonic_indoor/line_counters"
REST_AREA_OCCUPANCY: Final = "tridonic_indoor/area_occupancy"
REST_PEOPLE_PER_MINUTE: Final = "tridonic_indoor/people_per_minute"
REST_MINUTES_OCCUPIED: Final = "tridonic_indoor/minutes_occupied"
REST_MEAN_OCCUPANCY_TIME: Final = "tridonic_indoor/mean_occupancy_time"
REST_QUEUE_OCCUPANCY_AND_TIME: Final = "tridonic_indoor/queue_occupancy_and_time"
REST_QUEUE_MEAN_TIME: Final = "tridonic_indoor/queue_mean_time"
REST_QUEUE_PER_MINUTE: Final = "tridonic_indoor/queue_occupancy_per_minute"
REST_AREAS_ALERT_STATUS: Final = "tridonic_indoor/areas_alert_status"
REST_LINES_ALERT_STATUS: Final = "tridonic_indoor/lines_alert_status"

# MQTT topics.
TOPIC_ALL_METADATA: Final = "tridonic_indoor/all_metadata"
TOPIC_AREAS_STATUS: Final = "tridonic_indoor/areas_status"
TOPIC_LINES_STATUS: Final = "tridonic_indoor/lines_status"
TOPIC_RUNTIME_STATUS: Final = "tridonic_indoor/status"
TOPIC_SOLUTION_INFO: Final = "edge/solution/info"

SUBSCRIBE_TOPICS: Final = (
    TOPIC_ALL_METADATA,
    TOPIC_AREAS_STATUS,
    TOPIC_LINES_STATUS,
    TOPIC_RUNTIME_STATUS,
    TOPIC_SOLUTION_INFO,
)

# Metadata block "type" values inside the all_metadata payload.
TYPE_LINE_COUNTERS: Final = "line_counters"
TYPE_AREA_OCCUPANCY: Final = "area_occupancy"
TYPE_PEOPLE_PER_MINUTE: Final = "people_per_minute"
TYPE_MINUTES_OCCUPIED: Final = "minutes_occupied"
TYPE_MEAN_DWELL_TIME: Final = "mean_dwell_time"
TYPE_QUEUE_OCCUPANCY_AND_TIME: Final = "queue_occupancy_and_time"
TYPE_PEOPLE_IN_QUEUE_PER_MINUTE: Final = "people_in_queue_per_minute"
TYPE_MEAN_QUEUE_TIME: Final = "mean_queue_time"

# Shape classes.
CLASS_LINE: Final = "Line"
CLASS_AREA: Final = "Area"
CLASS_QUEUE: Final = "Queue"

# Alert status value reported by the device when a threshold is exceeded.
ALERT_VALUE_PROBLEM: Final = "red"
