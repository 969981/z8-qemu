# Nikon Z8 C3.12 — second-pass static analysis

> Source: user's original `Z_8_0312.bin` (99,051,117 bytes; SHA-256 `d662dd9dd5da937cb418162c238065e918dcefafd47b47537c3f934d39e83037`).
> This is read-only **static evidence**, not proof of a working Z8 C3.12 QEMU boot or a complete EG decryption.

## 1. Verification boundary

The recovered legacy XOR scheme uses 256-byte T1/T2/T3 tables. T1 and T2 are fully recovered, matching the known public-tool hashes; **193 of 256 T3 indices** have direct padding evidence and **63 do not**. Ranking the T3 guesses by most frequent zero / 0xFF values produces **6 disagreements among the 193 directly observed positions**. Thus statistical guesses for the missing indices **cannot be promoted to verified key material**.

- CRC16 **PASS**: `ex2070_030000.bi`, `_tpj01_0210.bin`, `li2070_031200.bi`.
- CRC16 **FAIL** with the current candidate key: `eg2070_031200.bi`, `vr2070_010100.bi`.
- Whole-package CRC also fails. Do not use the candidate EG for QEMU or for a camera upgrade.
- [T3 index evidence (CSV)](t3_index_confidence.csv) lists direct observations, statistical candidates, zero/FF support and alternative scores.

## 2. Linux image and boot path

The CRC-verified `li2070_031200.bi` (SHA-256 `6fde4f443e0c56f5153013d531f6f1ec7f7536732cc50b9067809a5b99ead8cf`) has a `NISI` header and Linux `4.14.224-ts-aarch64`. The gzip/newc initramfs contains **821** CPIO entries (272 regular files).

The boot scripts provide an explicit, reviewable startup chain:

```
BusyBox init
  -> /etc/inittab
  -> /etc/init.d/rcS
  -> S00-config-hotplug, S01-create-devices, S02-mount, S03-modules
  -> S11-LaMainApp
  -> /usr/bin/LaMainApp &
```

The six `La*` application files present in `/usr/bin` are stripped AArch64 ELF64 ET_EXEC executables. Their entry points and dynamic libraries were parsed from the **actual binaries**:

| Program | Entry | Additional linked components |
| --- | ---: | --- |
| `LaMainApp` | `0x4021cc` | pthread, C++ runtime, libc |
| `LaLiveView` | `0x402378` | pthread, C++ runtime, libc |
| `LaFtpClient` | `0x4027e4` | libcurl, libssh2, libssl 1.1, zlib |
| `LaIfCtrl` | `0x403338` | libnl-3, libnl-genl-3 |
| `LaNetCameraCtrl` | `0x401f3c` | pthread, C++ runtime, libc |
| `LaSyncRelease` | `0x40205c` | libnl-3, libnl-genl-3 |

`LaMainApp` references the pathname `/usr/bin/LaHttpServer`, but that binary is **not present in this extracted initramfs**. This does not prove that the firmware cannot supply it by another filesystem or at runtime.

All six programs contain `/tmp/LaMainApp_unix_socket` and `/dev/oscom_memhelper` strings. Relevant drivers in the rootfs include `oscom_memhelper.ko` and `oscom_inthelper.ko`. This is concrete IPC/device-interface evidence, not a fully reversed message protocol.

## 3. Two verified device trees in LI

Two FDT blobs are present at **LI-relative offsets** `0xF15000` and `0xF16000`, with lengths **3141** and **3168** bytes. Each parses into **22 nodes** and advertises an ARM Cortex-A53 CPU node `cpu@3`; the node alone does not establish the total SoC CPU count.

| SDHCI property | DTB at 0xF15000 | DTB at 0xF16000 |
| --- | --- | --- |
| `fixed-1.8v` | present | absent |
| `fixed-3.3v` | absent | present |
| `uhs-limit-sdr104` | present | absent |
| `uhs-limit-sdr12` | absent | present |
| `clock-limit` | absent | 50,000,000 Hz |

**These are the only five differing DTB properties** found by comparing the parsed node paths and properties. Their exact firmware selection condition is not verified.

Device-tree hardware evidence (physical address):

| Node | Physical address | Comment |
| --- | --- | --- |
| GICv3 | `0x0D000000` | interrupt controller |
| UART | `0x0F000000` | `nikon,nkj-uart` |
| SDHCI | `0x17830000` | `nikon,xxx-sdhci` |
| USB xHCI | `0x17880000` | `socionext,sc2007-xhci` |
| OS_COM reserved memory | `0xA0F000000` | length `0x2000` |
| shared memory | `0xA0F002000` | length `0x7FD000` |

These addresses and compatible strings are useful for the Z8 QEMU device-model audit. They are from the Linux-side DTBs and **must not automatically be assumed to be EG firmware virtual addresses**.

## 4. Scope / next verification gates

1. Recover the **63 missing T3 positions** using additional compatible stock firmware samples; the public [nikon-fw-key-tool](https://github.com/WonderLantern/nikon-fw-key-tool) documents a known-sufficient four-image set.
2. Require **all five module CRCs plus package CRC** before exporting the EG or VR for analysis.
3. Independently compare validated C3.11 and C3.12 modules, beginning with hashes and binary diff; do not infer the lens-hang patch from a 3.12-only sample.
4. Compare the two FDT modes against QEMU's SDHCI model, and identify how the guest selects each variant.
5. Trace `LaMainApp` process creation and OS_COM IOCTL/mmap behavior in a sandbox; network-service binaries alone do not demonstrate externally reachable services.

The research scripts and accompanying machine-readable device-tree and ELF inventories were produced locally. As with the rest of this repository, no Nikon proprietary binary is included in this Markdown report.
