"""Parse FalcoSENSE MQTT payloads into the accumulated device state.

Every parser function mutates the passed-in :class:`FalcoSenseState` and never
raises on partially shaped data: the device is a prototype and omits blocks for
shape types that are not commissioned.
"""

from __future__ import annotations

from typing import Any

from .const import (
    ALERT_VALUE_PROBLEM,
    TYPE_AREA_OCCUPANCY,
    TYPE_LINE_COUNTERS,
    TYPE_MEAN_DWELL_TIME,
    TYPE_MEAN_QUEUE_TIME,
    TYPE_MINUTES_OCCUPIED,
    TYPE_PEOPLE_IN_QUEUE_PER_MINUTE,
    TYPE_PEOPLE_PER_MINUTE,
    TYPE_QUEUE_OCCUPANCY_AND_TIME,
)
from .models import Area, FalcoSenseState, Line, Queue, ShapeGeometry


def _counter_by_name(shape: dict[str, Any], name: str) -> int | None:
    """Return the value of a named entry in a shape's ``counters`` list."""
    for counter in shape.get("counters", []):
        if counter.get("name") == name:
            return counter.get("value")
    return None


def _area(state: FalcoSenseState, shape: dict[str, Any]) -> Area:
    uid = shape["uid"]
    area = state.areas.get(uid)
    if area is None:
        area = Area(uid=uid, label=shape["label"], zone_id=shape["zoneID"])
        state.areas[uid] = area
    return area


def _line(state: FalcoSenseState, shape: dict[str, Any]) -> Line:
    uid = shape["uid"]
    line = state.lines.get(uid)
    if line is None:
        line = Line(uid=uid, label=shape["label"], zone_id=shape["zoneID"])
        state.lines[uid] = line
    return line


def _queue(state: FalcoSenseState, shape: dict[str, Any]) -> Queue:
    uid = shape["uid"]
    queue = state.queues.get(uid)
    if queue is None:
        queue = Queue(uid=uid, label=shape["label"], zone_id=shape["zoneID"])
        state.queues[uid] = queue
    return queue


def _apply_block(state: FalcoSenseState, block: dict[str, Any]) -> None:
    block_type = block.get("type")
    shapes = block.get("shapes", [])
    if block_type == TYPE_LINE_COUNTERS:
        for shape in shapes:
            line = _line(state, shape)
            line.people_in = _counter_by_name(shape, "In")
            line.people_out = _counter_by_name(shape, "Out")
    elif block_type == TYPE_AREA_OCCUPANCY:
        for shape in shapes:
            _area(state, shape).occupancy = shape.get("counter")
    elif block_type == TYPE_PEOPLE_PER_MINUTE:
        for shape in shapes:
            _area(state, shape).people_per_minute = shape.get("counter")
    elif block_type == TYPE_MINUTES_OCCUPIED:
        for shape in shapes:
            _area(state, shape).minutes_occupied = shape.get("counter")
    elif block_type == TYPE_MEAN_DWELL_TIME:
        for shape in shapes:
            _area(state, shape).mean_dwell_time = shape.get("counter")
    elif block_type == TYPE_QUEUE_OCCUPANCY_AND_TIME:
        for shape in shapes:
            queue = _queue(state, shape)
            queue.occupancy = _counter_by_name(shape, "Occupancy")
            queue.average_waiting_time = _counter_by_name(shape, "Average waiting time")
    elif block_type == TYPE_PEOPLE_IN_QUEUE_PER_MINUTE:
        for shape in shapes:
            _queue(state, shape).people_per_minute = shape.get("counter")
    elif block_type == TYPE_MEAN_QUEUE_TIME:
        for shape in shapes:
            _queue(state, shape).mean_queue_time = shape.get("counter")


def apply_all_metadata(state: FalcoSenseState, payload: dict[str, Any]) -> None:
    """Apply the consolidated ``all_metadata`` payload."""
    for block in payload.get("data", []):
        _apply_block(state, block)


def _alert(entry: dict[str, Any]) -> bool:
    return entry.get("value") == ALERT_VALUE_PROBLEM


def apply_areas_status(state: FalcoSenseState, payload: dict[str, Any]) -> None:
    """Apply the ``areas_status`` alert payload, matching areas by uid."""
    for info in payload.values():
        area = state.areas.get(info.get("uid"))
        if area is None:
            continue
        for entry in info.get("alerts", []):
            name = entry.get("name")
            if name == "occupancy_status":
                area.occupancy_alert = _alert(entry)
            elif name == "dwell_time_status":
                area.dwell_time_alert = _alert(entry)
            elif name == "dwell_avg_time_status":
                area.dwell_avg_time_alert = _alert(entry)


def apply_lines_status(state: FalcoSenseState, payload: dict[str, Any]) -> None:
    """Apply the ``lines_status`` alert payload, matching lines by uid."""
    for info in payload.values():
        line = state.lines.get(info.get("uid"))
        if line is None:
            continue
        for entry in info.get("alerts", []):
            name = entry.get("name")
            if name == "in_status":
                line.in_alert = _alert(entry)
            elif name == "out_status":
                line.out_alert = _alert(entry)


def _point(entry: dict[str, Any]) -> tuple[float, float]:
    return (entry["x"], entry["y"])


def apply_annotations(state: FalcoSenseState, payload: dict[str, Any]) -> None:
    """Apply the ``annotations`` payload, replacing the known shape geometry.

    Coordinates are normalized to the camera frame (each component ~0..1). The
    payload is self-contained (label, color, type), so it does not depend on the
    metadata shapes having been received yet.
    """
    geometry: list[ShapeGeometry] = []
    for shape in payload.get("shapes", []):
        is_line = shape.get("type") == "line"
        item = ShapeGeometry(
            uid=shape.get("uid", ""),
            label=shape.get("label", ""),
            color=shape.get("color", {}).get("hex", "#FFFFFF"),
            is_line=is_line,
        )
        if is_line:
            if "start" not in shape or "end" not in shape:
                continue
            item.start = _point(shape["start"])
            item.end = _point(shape["end"])
        else:
            item.points = [_point(p) for p in shape.get("points", [])]
        geometry.append(item)
    state.annotations = geometry


def apply_runtime_status(state: FalcoSenseState, payload: dict[str, Any]) -> None:
    """Apply the runtime ``status`` payload (1 = running)."""
    if "status" in payload:
        state.device.running = payload["status"] == 1


def apply_solution_info(state: FalcoSenseState, payload: dict[str, Any]) -> None:
    """Apply the ``edge/solution/info`` payload (uptime and firmware)."""
    if "uptime" in payload:
        state.device.uptime = payload["uptime"]
    if "version" in payload:
        state.device.firmware_version = payload["version"]
