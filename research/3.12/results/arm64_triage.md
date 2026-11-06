# Z8 C3.12 AArch64 static triage

All source containers passed module/package CRC verification before this analysis.
Known sites are addresses from the **C3.11** QEMU boot harness; their C3.12 identity is unverified.

| C3.11 site | Old address | 64 bytes unchanged? | Different bytes |
| --- | --- | --- | ---: |
| boot_entry | `0x40160000` | True | 0 |
| adc_ready | `0x4033db98` | True | 0 |
| power_status | `0x40d57a90` | False | 1 |
| system_power_event | `0x40d67260` | True | 0 |
| battery_callback | `0x41181504` | False | 59 |
| lens_controller_reply | `0x4106e690` | False | 57 |
| menu_event_1 | `0x40d66034` | True | 0 |
| menu_event_2 | `0x40d55da0` | False | 1 |
| menu_event_3 | `0x40d5eb7c` | True | 0 |
| half_shutter_1 | `0x40d271e4` | False | 1 |
| half_shutter_2 | `0x40d26d7c` | False | 1 |
| half_shutter_3 | `0x40d3003c` | True | 0 |
| framebuffer_event | `0x40fac9bc` | False | 61 |
| ui_event | `0x40d57118` | False | 1 |

Linux LI exact byte differences: **2**.

Sparse candidates with valid-looking AArch64 words: **4215** (only the first 70 are listed in JSON).

**These are not verified function boundaries or an identified lens-fix call path.**
