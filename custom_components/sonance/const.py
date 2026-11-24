"""Constants for the Sonance DSP integration."""
from __future__ import annotations

from dataclasses import dataclass

from .protocol import CHANNEL_NAMES, GROUP_LETTERS

DOMAIN = "sonance"
DEFAULT_PORT = 52000
CONF_MODEL = "model"

MODEL_DSP2_150 = "DSP2-150"
MODEL_DSP2_750 = "DSP2-750"
MODEL_DSP8_130 = "DSP8-130"

_OPEN = [f"{n}-OPEN" for n in range(42, 50)]

_PRESETS_150 = [
    "FLAT", "DOS System", "AS38RS", "BPS6", "AS68RS+BPS8 System", "AS68RS", "BPS8",
    "IS2", "IS4", "IS4SST", "ISW",
    "VP46", "VP48", "VP46R", "VP48R",
    "VP66", "VP68", "VP64R", "VP66R", "VP68R", "VP66 TL", "VP66R TL",
    "VP86", "VP88", "VP86R", "VP88R",
    "VP46R~SST+SUR", "VP66~SST+SUR", "VP66R~SST+SUR", "VP86R~SST+SUR",
    "VP65 XT", "VP65R XT", "VP65S XT", "VP65R~SST-XT",
    "VP85W", "VP85RW", "VP10SUB", "VP10SUB NC",
    "SONARRAY", "MARINER 82", "MARINER 63", "MARINER 62",
] + _OPEN

_PRESETS_750 = [
    "FLAT",
    "LS48~V10", "LS48~V10+3", "LS48~V10+6",
    "LS48~LS12E", "LS48~LS12E+3", "LS48~LS12E+6",
    "LS68~V10", "LS68~V10+3", "LS68~V10+6",
    "LS68~LS12E", "LS68~LS12E+3", "LS68~LS12E+6",
    "LS47~LS10", "LS47~LS10+3", "LS47~LS10+6",
    "LS47~V10", "LS47~V10+3", "LS47~V10+6",
    "LS47~LS12E", "LS47~LS12E+3", "LS47~LS12E+6",
    "LS47", "LS48", "LS68",
    "LS10", "LS10+3", "LS10+6",
    "V10", "V10+3", "V10+6",
    "LS12E", "LS12E+3", "LS12E+6",
    "IS4C", "FMS860", "FMS660", "FMS530", "CM860", "CM660", "CT10", "CT8",
    "VP12SUB-NC",
] + [f"{n}-OPEN" for n in range(43, 50)]


@dataclass(frozen=True)
class ModelInfo:
    groups: tuple[str, ...]
    sources: int
    channels: tuple[str, ...]
    presets: tuple[str, ...]


MODELS: dict[str, ModelInfo] = {
    MODEL_DSP2_150: ModelInfo(tuple(GROUP_LETTERS[:2]), 2, tuple(CHANNEL_NAMES[:2]), tuple(_PRESETS_150)),
    MODEL_DSP2_750: ModelInfo(tuple(GROUP_LETTERS[:2]), 2, tuple(CHANNEL_NAMES[:2]), tuple(_PRESETS_750)),
    MODEL_DSP8_130: ModelInfo(tuple(GROUP_LETTERS), 4, tuple(CHANNEL_NAMES), tuple(_PRESETS_150)),
}
