import importlib.util, pathlib, sys

p = pathlib.Path(__file__).parent.parent / "custom_components/sonance/protocol.py"
spec = importlib.util.spec_from_file_location("protocol", p)
proto = importlib.util.module_from_spec(spec)
sys.modules["protocol"] = proto
spec.loader.exec_module(proto)


def test_frames():
    assert proto.global_frame(proto.volume_code(-70)) == b"\xff\x55\x01\x71"
    assert proto.target_frame(proto.volume_code(12), proto.group_index("A")) == b"\xff\x55\x02\xc3\x00"
    assert proto.volume_code(0) == 0xB7
    assert proto.target_frame(proto.CMD_PRESET_BASE + 49, proto.channel_index("4R")) == b"\xff\x55\x02\x61\x0f"


def test_parsers():
    assert proto.parse_power("Power status :On") is True
    assert proto.parse_volume("Cmd:Volume      ,Group:A Vol=-12 d", "A") == -12
    assert proto.parse_mute("Cmd:MuteState   ,Group:B Mute=off", "B") is False
    assert proto.parse_source("Cmd:Source2     ,Group:A Src1=Input 1L", "A") == (2, "Input 1L")
    assert proto.parse_channel_value(
        proto.RE_SHORT, "Cmd:AmpShortCir :No short,Channel Output 1L", "1L") == "No short"


def test_volume_mapping():
    assert proto.volume_from_ha(0) == -70 and proto.volume_from_ha(1) == 12
