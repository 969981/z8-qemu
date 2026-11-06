# Nikon Z8 firmware C 3.12 research

This branch is a **research worktree**, not a boot-qualified QEMU C3.12 port.
The existing QEMU launchers and `docs/firmware.md` still require the original
**C3.11 MAIN payload** (81,807,709 bytes, SHA-256
`2b43a31c9de838f84b12416de4348a7004e65be07f853ec56ec2b10f3a8e3853`).
Do not relax those checks or feed the encrypted `Z_8_0312.bin` directly to QEMU.

## Input sample

- Official Nikon download: https://downloadcenter.nikonimglib.com/en/download/fw/608.html
- File name: `Z_8_0312.bin`
- Size: **99,051,117 bytes**
- SHA-256: `d662dd9dd5da937cb418162c238065e918dcefafd47b47537c3f934d39e83037`
- Status: source file inspected locally; **the proprietary Nikon firmware is not redistributed in this public repository**.
- Keep a local copy at `.local/firmware/Z_8_0312.bin` (ignored by git).

Verify your own downloaded copy:

```bash
sha256sum .local/firmware/Z_8_0312.bin
```

## Findings

- Recovered a 5-entry firmware component directory: `ex`, `_tpj01`, `eg`, `vr`, `li`.
- Three component payloads passed independently calculated CRC16: `ex`, `_tpj01`, `li`.
- `eg` (main engine) and `vr` (IBIS) **did not pass** CRC16 with the candidate XOR key; no complete verified executable was produced.
- The verified Linux image contains Linux 4.14.224-ts-aarch64, an initramfs with 821 entries, including 173 ELF files, and Nikon services such as `LaMainApp`, `LaLiveView`, and `LaNetCameraCtrl`.
- For interpreting the 3.11 → 3.12 lens-hang fix, a verified C3.11 package and byte-level comparison are still required.

## Research artifacts

- [`Z8_3.12_固件结构分析.md`](Z8_3.12_固件结构分析.md): annotated findings and confidence levels.
- [`Z8_v3.12_initramfs_manifest.csv`](Z8_v3.12_initramfs_manifest.csv): 821 initramfs entries and their metadata / hashes.

**Limitations:** Do not flash any candidate/decrypted firmware to a physical camera.
Nikon's download page identifies the camera firmware as copyright Nikon and states reproduction is not permitted. Keep firmware inputs local and obtain them from Nikon directly.
