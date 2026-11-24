# Sonance DSP amplifier (Home Assistant)

Local control of Sonance DSP2-150, DSP2-750 and DSP8-130 amplifiers over TCP (port 52000).

Install via HACS (custom repository) or copy `custom_components/sonance` into your HA config, restart, then add **Sonance DSP Amplifier** under Settings → Devices & services.

Entities: a media player per group (power, volume, mute, source), unit power switch, per-channel EQ preset select, stereo/mono switch, and short-circuit / over-temperature diagnostics.

Protocol spec: `DSP_IP_Codes_SONANCE.xlsx`.
