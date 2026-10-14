"""Tests for the FalcoSENSE payload parser, using captured device payloads."""

from __future__ import annotations

from falcosense.models import FalcoSenseState
from falcosense.parser import (
    apply_all_metadata,
    apply_areas_status,
    apply_lines_status,
    apply_runtime_status,
    apply_solution_info,
)

ALL_METADATA = {
    "data": [
        {
            "type": "line_counters",
            "reset": False,
            "timestamp": "2026-10-14T08:29:52Z",
            "shapes": [
                {
                    "class": "Line",
                    "label": "Line 1",
                    "uid": "line-uid",
                    "zoneID": 1,
                    "counters": [
                        {"name": "In", "value": 8},
                        {"name": "Out", "value": 5},
                    ],
                }
            ],
        },
        {
            "type": "area_occupancy",
            "shapes": [
                {
                    "class": "Area",
                    "label": "Area 1",
                    "uid": "area-uid",
                    "zoneID": 1,
                    "counter": 2,
                },
            ],
        },
        {
            "type": "minutes_occupied",
            "shapes": [
                {
                    "class": "Area",
                    "label": "Area 1",
                    "uid": "area-uid",
                    "zoneID": 1,
                    "counter": 39,
                },
            ],
        },
        {
            "type": "mean_dwell_time",
            "shapes": [
                {
                    "class": "Area",
                    "label": "Area 1",
                    "uid": "area-uid",
                    "zoneID": 1,
                    "counter": 12,
                },
            ],
        },
        {
            "type": "queue_occupancy_and_time",
            "shapes": [
                {
                    "class": "Queue",
                    "label": "Queue 1",
                    "uid": "q-uid-queue",
                    "zoneID": 1,
                    "counters": [
                        {"name": "Occupancy", "value": 2},
                        {"name": "Average waiting time", "value": 871},
                    ],
                },
            ],
        },
    ]
}


def test_all_metadata_populates_shapes() -> None:
    """The consolidated payload creates lines, areas and queues by uid."""
    state = FalcoSenseState()
    apply_all_metadata(state, ALL_METADATA)

    line = state.lines["line-uid"]
    assert (line.label, line.zone_id, line.people_in, line.people_out) == (
        "Line 1",
        1,
        8,
        5,
    )
    area = state.areas["area-uid"]
    assert (area.occupancy, area.minutes_occupied, area.mean_dwell_time) == (2, 39, 12)
    queue = state.queues["q-uid-queue"]
    assert (queue.occupancy, queue.average_waiting_time) == (2, 871)


def test_area_and_line_alert_status() -> None:
    """Alert payloads mark problem states by uid; red means alerting."""
    state = FalcoSenseState()
    apply_all_metadata(state, ALL_METADATA)

    apply_areas_status(
        state,
        {
            "Area 1": {
                "uid": "area-uid",
                "alerts": [
                    {"name": "occupancy_status", "value": "red"},
                    {"name": "dwell_time_status", "value": "green"},
                    {"name": "dwell_avg_time_status", "value": "green"},
                ],
            }
        },
    )
    apply_lines_status(
        state,
        {
            "Line 1": {
                "uid": "line-uid",
                "alerts": [
                    {"name": "in_status", "value": "green"},
                    {"name": "out_status", "value": "red"},
                ],
            }
        },
    )

    area = state.areas["area-uid"]
    assert area.occupancy_alert is True
    assert area.dwell_time_alert is False
    line = state.lines["line-uid"]
    assert line.in_alert is False
    assert line.out_alert is True


def test_unknown_uid_in_status_is_ignored() -> None:
    """Status for an uncommissioned/unknown shape must not create entries."""
    state = FalcoSenseState()
    apply_areas_status(
        state,
        {
            "Ghost": {
                "uid": "nope",
                "alerts": [{"name": "occupancy_status", "value": "red"}],
            }
        },
    )
    assert state.areas == {}


def test_device_info_payloads() -> None:
    """Runtime status and solution info update device health fields."""
    state = FalcoSenseState()
    apply_runtime_status(state, {"status": 1})
    apply_solution_info(state, {"uptime": 74582, "version": "f2.0.16"})
    assert state.device.running is True
    assert state.device.uptime == 74582
    assert state.device.firmware_version == "f2.0.16"
