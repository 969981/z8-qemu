# Nikon Z8 C3.12: runtime and independent feature acceptance

This is an evidence ledger for the **3.12 research branch**. It does not
license vendor binaries for redistribution or authorize flashing a camera.

## Tested baseline and revision

- The original Z8 C3.11 and C3.12 packages both passed all five individual
  CRC16 module checks and their package CRC. Their original binaries stayed in
  ephemeral CI storage.
- C3.11 EG SHA-256: `2b43a31c9de838f84b12416de4348a7004e65be07f853ec56ec2b10f3a8e3853`.
- C3.12 EG SHA-256: `ec6f069e38f7bc4635fc7e6e9ae6304b3901953fadfdb9f33f011e4485b5b867`.
- C3.11 & C3.12 both completed the *previous bounded QEMU headless smoke*
  (exit code 0, 661 and 671 passed harness checks, respectively). Evidence:
  [run 42319882964](https://github.com/969981/z8-qemu/actions/runs/42319882964)
  and [boot_status.json](results/boot_status.json).
- **Do not promote this success to general camera functional parity.**

## Separate and deliberately narrow acceptance levels

| Level | Test and evidence | Interpretation |
| --- | --- | --- |
| L0 | Independent full stock decryption, individual CRCs and package CRC | Valid component bytes; no runtime assertion |
| L1 | C3.11 and C3.12 headless smoke in QEMU 11.1.1, original guest bytes | Both completed the existing bounded boot/menu diagnostic |
| L2 | `runtime_evidence.json`, validated by `ci/verify_runtime_evidence.py` | Actual halted CPU PC at ADC and lens, lens reply status 0, framebuffer event hit; **separate from L1** |
| L3 | `native_ex_features.json`, validated by `ci/summarize_native_features.py` | Original EX03.00 firmware and MAIN3.12 communication, Movie lever input and observed return to Photo; not real lens AF |
| L4 | `still_capture_evidence.json` and subsequent independent NEF/pixel decoder audit | Guest-created NEF on virtual exFAT; a file alone is *not* validated RAW capture |
| L5 | Separate recorded movie file, playback, frame/audio and codec verification | **Not established by boot/menu or Movie mode switching** |
| Physical | Controlled real-lens AF/aperture and camera operation | Cannot be certified by QEMU |

The original 3.11 workflow always runs first. C3.12's shifted breakpoints are
opt-in and require checking the actual engine SHA-256. Three high-confidence
static relocation candidates were identified:
`ADC 0x41181504 → 0x4118156C`,
`lens 0x4106E690 → 0x4106E6F8`, and
`framebuffer 0x40FAC9BC → 0x40FACA24`.
The remaining sites retain original addresses based on static evidence.

## Regression workflows and input constraints

- [`z8-312-verify.yml`](../../.github/workflows/z8-312-verify.yml)
  (repository-root workflow path): cross-firmware key recovery and ARM64
  source-backed address localization.
- [`z8-312-boot-smoke.yml`](../../.github/workflows/z8-312-boot-smoke.yml)
  (repository-root workflow path): exact QEMU 11.1.1 build, original engine and
  EX component hashes, baseline then C3.12 testing, and the L2/L3/L4 experiments.
- The source-only checks include `test_z8_site_profiles.py`,
  `test_z8_runtime_evidence.py`, `test_z8_native_features.py` and
  `test_z8_still_capture_evidence.py`.
- The EX test uses the *actual original* EX03.00, matching
  SHA-256 `8ce129fa3689d1d619f25ba1c44a3a9f1964c76fe77b95adeb4ea912463c8c63`.
- Still photography uses a synthetic Bayer input and an ephemeral, sparse
  8-GiB exFAT card; it attempts the guest's lossless NEF write path. Card
  presence alone never marks L4 complete. No card or generated NEF is
  retained as a public artifact.

### Honesty gates

The active strict evidence checks and independent EX/NEF experiments are
**not marked passed in this ledger until their corresponding GitHub Actions
runs finish and their JSON result records meet the acceptance conditions**.
Even after a successful L2/L3, independent output validation is necessary
for actual still photo and encoded movie results.

Do not treat result metadata, a single moved instruction, static matching,
frame counters, or a UI mode label as proof of physical camera equivalence.
