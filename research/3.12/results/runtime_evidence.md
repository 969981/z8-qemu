# Nikon Z8 3.11 / 3.12 — real guest PC acceptance evidence

Actual vCPU PC stops, checks and lens reply words are parsed from QEMU receipts.
This report **does not** establish photo capture, video recording or physical lens operation.

| Check | C3.11 | C3.12 |
| --- | ---: | ---: |
| Expected ADC breakpoint actual hits | 1 | 1 |
| Lens callback actual hits | 2 | 2 |
| Valid lens reply status=0 | 2 | 2 |
| Framebuffer guest PC hits | 1 | 1 |
| Model checks failed | 0 | 0 |
| Bounded boot evidence passed | True | True |

**Both versions passed:** True.

A fully-qualified camera requires separately recorded still photo, movie and physical-lens tests.
