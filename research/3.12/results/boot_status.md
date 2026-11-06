# Nikon Z8 C3.12 QEMU bounded boot probe

The firmware images were only used in an isolated CI runner.
The baseline was tested first; 3.12 SHA checks were changed only in the ephemeral runner copy.
No guest instructions were patched, and no real camera is involved.

| Test | Exit status | Finished smoke? |
| --- | ---: | --- |
| C3.11 | 0 | True |
| C3.12 | 1 | False |

Qualified headless smoke in this runner: **False**.

Exit 124 means timeout. A failed smoke may be caused by hardcoded C3.11 boot breakpoints, Linux host differences, or missing hardware emulation; examine test logs before attributing it to the firmware.
