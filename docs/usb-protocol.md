# Indoor Sky USB contract (unchanged)

Source of truth: packed structs and serializers in src/main.cpp and the
Electric Sea router/server.js consumeUsbBytes parser. Multi-byte values use
ESP32 little-endian layout; floats are IEEE 754 binary32. USB CDC carries a byte
stream with interleaved scalar, audio and status frames; reads can split frames.
Resynchronize by magic and validate declared lengths before decoding.

## Scalar: INSK, version 1

76-byte packed header followed by bmeCount 24-byte BmeSamples, then audioCount
16-byte AudioSamples. No outer length prefix or delimiter.

| Offset | Type | Field |
| --- | --- | --- |
| 0 | char[4] | INSK |
| 4 | u8/u8/u16 | version=1, flags, headerBytes=76 |
| 8 | u32 | packetSequence |
| 12 | u64 | sendTimeUs |
| 20 | u16/u16 | bmeCount, audioCount |
| 24 | u32/u32 | bmeOverruns, audioOverruns |
| 32 | u16/u16 | bmeHzX10, audioHzX10 |
| 36 | u16/u16/u16/u16 | bmeQueue, audioQueue, transportQueued, reserved |
| 44 | u32 | transportDrops |
| 48 | u16 | scheduledHzX10 |
| 50 | u32 | uptimeMs |
| 54 | i16 | wifiRssiDbm |
| 56 | u16/u16 | wifiReconnects, reserved2 |
| 60 | u32/u32/u32/u32 | oscSendFailures, oscSendAvgUs, oscSendMaxUs, oscSendStalls |

BmeSample: u32 sequence, u64 timeUs, f32 temperature (C), humidity (%), pressure
(hPa). AudioSample: u32 sequence, u64 timeUs, f32 rmsDb (dBFS). Timestamps are
device microseconds, not Unix wall time. Requested BME/RMS rates remain 100/250 Hz;
batch interval is 63 ms. Current batch maxima are eight BME and sixteen RMS samples.

## Audio: ESAU

32-byte PcmPacketHeader: magic[4], u8 version/channels/bitsPerSample/flags,
u32 packetSequence, u64 firstSampleTimeUs, u32 sampleRate, u16 sampleCount,
u16 headerBytes, u32 queueDrops. Mono 16 kHz; current samples per packet: 640.
16-bit PCM payload is sampleCount signed little-endian i16 values. Existing
4-bit IMA ADPCM encoding uses headerBytes=36 with i16 predictor, u8 index,
u8 reserved, followed by ceil((sampleCount-1)/2) packed bytes. Keep encoder and
router decoder nibble ordering/version handling unchanged.

## Status and commands

INJS: four-byte magic, u32 JSON byte length, then UTF-8 status JSON. Identity,
health, rates, counters and existing keys are unchanged. Router caches fresh USB
status at GET /indoor-sky/status without a Wi-Fi HTTP fallback in rf-router.

Host-to-device commands are exactly four ASCII bytes without newline:

- INRS: reboot.
- INP1: enable USB audio, disable network PCM and reset PCM queue.
- INP0: disable USB audio and reset PCM queue.

Do not rename node indoor-sky, OSC /batch/indoor-sky/{temperature,humidity,pressure,rms},
PCM stream pcm/indoor-sky/audio, router /indoor-sky routes, firmware HTTP endpoints
or status fields. Network OSC/PCM ports remain 5005/5007. Electric Sea owns parsing,
pacing and archive forwarding; Weather Brain retains existing IDs/schema/APIs.
