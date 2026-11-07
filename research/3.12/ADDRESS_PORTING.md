# Nikon Z8 C3.12: isolated boot breakpoint port (research)

This is an **experimental** port on branch `3.12`. It preserves the
production C3.11 behavior and does not create a flashable firmware image.

## Evidence and input requirements

- C3.11 Engine: `2b43a31c9de838f84b12416de4348a7004e65be07f853ec56ec2b10f3a8e3853`
- C3.12 Engine: `ec6f069e38f7bc4635fc7e6e9ae6304b3901953fadfdb9f33f011e4485b5b867`
- Both source packages passed **5 component CRCs and a package CRC**.
- The original C3.11 bounded headless smoke passes; the previous C3.12 test timed
  out at a hard-coded `0x41181504` breakpoint.
- `results/relocation_candidates.json` provides 26 evidence rows, covering
  `tools/boot_z8.py`, `tools/deliver_mcu_frame.py` and `tools/receive_mcu_tx.py`.

| Named site | C3.11 | C3.12 static candidate | Qualification |
| --- | --- | --- | --- |
| Battery/ADC callback | `0x41181504` | `0x4118156C` | two-sided identical neighbors; **runtime unverified** |
| Lens controller reply | `0x4106E690` | `0x4106E6F8` | two-sided identical neighbors; **runtime unverified** |
| Framebuffer event | `0x40FAC9BC` | `0x40FACA24` | two-sided identical neighbors; **runtime unverified** |

The remaining 23 C3.11 breakpoints require no *static address shift* in this
first-pass evidence: 18 have the same 64 bytes; 5 remain at the same offset
with nearby byte differences. This does **not** prove runtime equivalence.

## Isolation and fail-closed behavior

1. `profiles/3.11.json` freezes the previously proven C3.11 address set.
2. `profiles/3.12.json` independently records 26 **unqualified** candidate PCs.
3. Without `Z8_C312_SITE_PROFILE`, `tools/boot_z8.py` still passes the
   original C3.11 literals unchanged to QEMU.
4. To test the 3.12 candidates, the caller must supply both environment
   variables `Z8_C312_SITE_PROFILE` pointing to the file and
   `Z8_C312_ALLOW_UNQUALIFIED_BOOT=1`; the helper checks the entire actual
   Engine SHA-256 before resolving *any* candidate.
5. Missing, misaligned or mismatched site records cause an error. The
   `unqualified_c312_site_profile` record in the QEMU test JSON explains which
   addresses were used.

The research workflow `z8-312-boot-smoke.yml` downloads the official source
firmware into the ephemeral runner, decrypts/validates it, builds QEMU 11.1.1,
runs C3.11 first without overrides, and only then tests 3.12 with the explicit
opt-in profile. It **does not publish vendor firmware or decrypted executables**.

## Remaining gates

- Verify the relocated ADC/MCU branch using the actual guest PC, SP, LR, and
  return/result registers, not only an instruction pattern.
- Verify lens reply payload equality and any new 3.12 control-flow branch.
- Verify framebuffer callback and UI/hardware models under the C3.12 guest.
- Do not modify or mark the `3.12` profile `runtime_qualified=true` without a
  recorded passing bounded smoke and a 3.11 baseline passing in the same CI.
- Full photo, video, AF and physical lens equivalence require independent
  tests even after a headless boot smoke passes.

## Reproduction

Use GitHub Actions **Nikon Z8 C3.12 QEMU bounded boot probe** in this
repository for dynamic testing. The exact firmware hashes, trace, result JSON
and validated vs unvalidated scope must accompany any reported outcome.
