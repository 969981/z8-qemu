# Nikon Z8 C3.12: verified partial unpack

Official firmware: https://downloadcenter.nikonimglib.com/en/download/fw/608.html

- Firmware: Z_8_0312.bin, 99,051,117 bytes
- SHA-256: d662dd9dd5da937cb418162c238065e918dcefafd47b47537c3f934d39e83037
- Recovered padding observations: T1 and T2 full; T3 193/256 indices directly observed.

| Module | Size including CRC | CRC16 result |
| --- | ---: | --- |
| ex2070_030000.bi | 524,290 | Verified (9b99) |
| _tpj01_0210.bin | 57,346 | Verified (8f0d) |
| eg2070_031200.bi | 81,807,711 | NOT VERIFIED: stored 12b4, candidate 266e |
| vr2070_010100.bi | 838,664 | NOT VERIFIED: stored 5bd4, candidate 4665 |
| li2070_031200.bi | 15,822,850 | Verified (8262) |

The CRC-verified LI module has SHA-256:
6fde4f443e0c56f5153013d531f6f1ec7f7536732cc50b9067809a5b99ead8cf

Its Linux image contains the 4.14.224-ts-aarch64 kernel and a CPIO
initramfs with 821 entries, including 272 regular files. Local unpack
produced the Linux kernel configuration, complete rootfs, and file hashes.

To unpack the verified LI payload supplied locally (no firmware is
distributed by this repository):

    python3 research/3.12/unpack_li.py li2070_031200.bi --out .local/z8_312_linux

For the full Nikon XOR decryption and checksum validators, see:
https://github.com/WonderLantern/nikon-fw-key-tool

The current QEMU emulator only has C3.11 firmware boot validation.
An encrypted C3.12 BIN is not a directly bootable EG payload.
Do not flash any partially decoded output.
