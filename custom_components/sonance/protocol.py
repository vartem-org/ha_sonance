"""Pure Sonance DSP IP protocol helpers (no Home Assistant imports)."""
from __future__ import annotations

import re

HEADER = b"\xff\x55"
VOL_MIN = -70
VOL_MAX = 12

GROUP_LETTERS = "ABCDEFGH"
CHANNEL_NAMES = ["1L", "1R", "2L", "2R", "3L", "3R", "4L", "4R"]

# Command codes
CMD_POWER_ON = 0x01
CMD_POWER_OFF = 0x02
CMD_POWER_TOGGLE = 0x03
CMD_VOL_UP = 0x04
CMD_VOL_DOWN = 0x05
CMD_MUTE_TOGGLE = 0x06
CMD_MUTE_ON = 0x07
CMD_MUTE_OFF = 0x08
CMD_SOURCE_BASE = 0x09  # 09..0C = source 1..4
CMD_STEREO_ON = 0x13
CMD_MONO_ON = 0x14
CMD_STEREO_MONO_TOGGLE = 0x15
CMD_Q_PRESET = 0x16
CMD_Q_SHORT = 0x17
CMD_Q_TEMP = 0x18
CMD_ASSIGN_GROUP_BASE = 0x21  # 21..28 = group A..H
CMD_PRESET_BASE = 0x30  # 30..61 = preset 0..49
CMD_Q_VOLUME = 0x10
CMD_Q_SOURCE = 0x11
CMD_Q_MUTE = 0x12
CMD_GROUP_ON = 0x65
CMD_GROUP_OFF = 0x66
CMD_GROUP_TOGGLE = 0x67
CMD_Q_POWER = 0x70
CMD_VOL_DIRECT_BASE = 0x71  # 71 = -70 dB .. C3 = +12 dB


def global_frame(cmd: int) -> bytes:
    """Frame affecting the unit or all groups."""
    return HEADER + bytes([0x01, cmd])


def target_frame(cmd: int, target: int) -> bytes:
    """Frame addressed to a group (0-7) or channel (8-15)."""
    return HEADER + bytes([0x02, cmd, target])


def group_index(group: str) -> int:
    return GROUP_LETTERS.index(group.upper())


def channel_index(channel: str) -> int:
    return 8 + CHANNEL_NAMES.index(channel.upper())


def volume_code(db: int) -> int:
    """Direct-volume command code for a dB value."""
    db = max(VOL_MIN, min(VOL_MAX, int(round(db))))
    return CMD_VOL_DIRECT_BASE + (db - VOL_MIN)


def volume_from_ha(level: float) -> int:
    """HA volume 0..1 -> dB."""
    return round(VOL_MIN + max(0.0, min(1.0, level)) * (VOL_MAX - VOL_MIN))


def volume_to_ha(db: float) -> float:
    return (max(VOL_MIN, min(VOL_MAX, db)) - VOL_MIN) / (VOL_MAX - VOL_MIN)


# ---- Feedback parsers (tolerant: match by key, not exact spacing) ----

RE_POWER = re.compile(r"Power status\s*:\s*(On|Off)", re.I)
RE_VOLUME = re.compile(r"Group:\s*([A-H])\s*Vol\s*=\s*(-?\d+)", re.I)
RE_SOURCE = re.compile(
    r"Cmd:Source(\d)\s*,\s*Group:\s*([A-H])\s*Src\d*\s*=\s*([^\r\n]*)", re.I
)
RE_MUTE = re.compile(r"Group:\s*([A-H])\s*Mute\s*=\s*(on|off)", re.I)
RE_PRESET = re.compile(r"DSP_Preset\s*:\s*(.*?)\s*,\s*Channel Output\s*(\d[LR])", re.I)
RE_SHORT = re.compile(r"AmpShortCir\s*:\s*(.*?)\s*,\s*Channel Output\s*(\d[LR])", re.I)
RE_TEMP = re.compile(r"AmpOverTemp\s*:\s*(.*?)\s*,\s*Channel Output\s*(\d[LR])", re.I)
RE_STEREO = re.compile(
    r"Cmd:Stereo\w*\s*:\s*(stereo|mono)\s*,\s*Channel Output\s*(\d[LR])", re.I
)


def parse_power(text: str) -> bool | None:
    m = RE_POWER.search(text)
    return None if not m else m.group(1).lower() == "on"


def parse_volume(text: str, group: str) -> int | None:
    for m in RE_VOLUME.finditer(text):
        if m.group(1).upper() == group.upper():
            return int(m.group(2))
    return None


def parse_source(text: str, group: str) -> tuple[int, str] | None:
    for m in RE_SOURCE.finditer(text):
        if m.group(2).upper() == group.upper():
            return int(m.group(1)), m.group(3).strip()
    return None


def parse_mute(text: str, group: str) -> bool | None:
    for m in RE_MUTE.finditer(text):
        if m.group(1).upper() == group.upper():
            return m.group(2).lower() == "on"
    return None


def parse_channel_value(regex: re.Pattern[str], text: str, channel: str) -> str | None:
    for m in regex.finditer(text):
        if m.group(2).upper() == channel.upper():
            return m.group(1).strip()
    return None
