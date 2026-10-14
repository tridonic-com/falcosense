"""Data models for the FalcoSENSE client.

Shapes (lines, areas, queues) are identified by their stable ``uid``. A single
device pushes several metadata blocks and separate alert-status topics; each
updates a subset of fields on the same shape, so the models are mutable and
accumulate state as messages arrive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# A point in normalized frame coordinates, each component in roughly 0..1.
Point = tuple[float, float]


@dataclass
class DeviceInfo:
    """Static and health information about the sensor."""

    name: str | None = None
    firmware_version: str | None = None
    timezone: str | None = None
    reset_time: str | None = None
    uptime: int | None = None
    running: bool | None = None


@dataclass
class Line:
    """A commissioned counting line with in/out crossings (resets daily)."""

    uid: str
    label: str
    zone_id: int
    people_in: int | None = None
    people_out: int | None = None
    in_alert: bool | None = None
    out_alert: bool | None = None


@dataclass
class Area:
    """A commissioned dwell area (region of interest)."""

    uid: str
    label: str
    zone_id: int
    occupancy: int | None = None
    people_per_minute: int | None = None
    minutes_occupied: int | None = None
    mean_dwell_time: float | None = None
    occupancy_alert: bool | None = None
    dwell_time_alert: bool | None = None
    dwell_avg_time_alert: bool | None = None


@dataclass
class Queue:
    """A commissioned queue with occupancy and waiting time."""

    uid: str
    label: str
    zone_id: int
    occupancy: int | None = None
    average_waiting_time: int | None = None
    people_per_minute: int | None = None
    mean_queue_time: float | None = None


@dataclass
class ShapeGeometry:
    """Drawable geometry for a commissioned shape, in normalized coordinates.

    A line uses ``start`` and ``end``; an area or queue uses ``points``.
    """

    uid: str
    label: str
    color: str
    is_line: bool
    start: Point | None = None
    end: Point | None = None
    points: list[Point] = field(default_factory=list)


@dataclass
class FalcoSenseState:
    """The full accumulated state of a FalcoSENSE device."""

    device: DeviceInfo = field(default_factory=DeviceInfo)
    lines: dict[str, Line] = field(default_factory=dict)
    areas: dict[str, Area] = field(default_factory=dict)
    queues: dict[str, Queue] = field(default_factory=dict)
    annotations: list[ShapeGeometry] = field(default_factory=list)
    # Latest debug camera frame (JPEG). Kept out of DeviceInfo so it is not
    # serialized into diagnostics.
    camera_frame: bytes | None = None
