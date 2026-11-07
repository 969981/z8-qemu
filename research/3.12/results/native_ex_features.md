# Nikon Z8 3.12 — independent original EX firmware feature probe

The EX03.00 and MAIN3.12 components are actual CRC-verified Nikon firmware.
Photo/Movie control contacts and frame counters use declared QEMU hardware fixtures.

| Feature | Result |
| --- | --- |
| Original EX MCU communication | False |
| Movie lever to Photo mode recovery | False |
| Actual saved NEF | False (not tested) |
| Actual saved movie file | False (not tested) |
| Physical lens AF/aperture | False (not tested) |

A clean execution without the relevant counters and original EX communication
does not automatically qualify a shooting or recording feature.
