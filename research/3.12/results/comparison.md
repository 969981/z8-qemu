# Nikon Z8 C3.11 vs C3.12 — verified container comparison

Generated from stock firmware with **all module CRCs and package CRC verified**.
The Z8 C3.11 engine also matched the known QEMU payload SHA-256.

| Component | 3.11 size | 3.12 size | Same payload? | Changed 4 KiB pages |
| --- | ---: | ---: | --- | ---: |
| _tpj01 | 57,344 | 57,344 | Yes | 0 |
| eg | 81,807,709 | 81,807,709 | No | 3,061 |
| ex | 524,288 | 524,288 | Yes | 0 |
| li | 15,822,848 | 15,822,848 | No | 1 |
| vr | 838,662 | 838,662 | Yes | 0 |

## Boundaries

Changed 4 KiB regions in comparison.json are **raw module-relative byte offsets**.
They are not automatically AArch64 function boundaries; changes may include resources,
tables, compressed data or moved code. Applying the provisional QEMU EG load address
0x40160000 is only meaningful after verifying module layout and execution mapping.

No original firmware bytes, derived decrypted payloads or XOR keys are published here.
No C3.12 QEMU boot has been established by this comparison.
