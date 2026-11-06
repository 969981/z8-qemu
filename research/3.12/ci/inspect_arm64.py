#!/usr/bin/env python3
"""Read-only ARM64 triage of CRC-verified Z8 C3.11/C3.12 engines.

The QEMU addresses below are C3.11 breakpoint/boot-site observations; matching
addresses in C3.12 are merely hypotheses until the guest runtime is verified.
Disassembly of raw data is NOT function identification. No firmware bytes are
emitted beyond one instruction mnemonic and operands for a bounded sample.
"""
import argparse
import json
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from compare_z8 import modules, BASE, BASELINE_SHA

KNOWN_SITES = {
    "boot_entry":0x40160000,
    "adc_ready":0x4033DB98,
    "power_status":0x40D57A90,
    "system_power_event":0x40D67260,
    "battery_callback":0x41181504,
    "lens_controller_reply":0x4106E690,
    "menu_event_1":0x40D66034,
    "menu_event_2":0x40D55DA0,
    "menu_event_3":0x40D5EB7C,
    "half_shutter_1":0x40D271E4,
    "half_shutter_2":0x40D26D7C,
    "half_shutter_3":0x40D3003C,
    "framebuffer_event":0x40FAC9BC,
    "ui_event":0x40D57118,
}
BRANCH = {"bl","blr","b","br","cbz","cbnz","tbz","tbnz","b.eq","b.ne","ret"}
md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)


def mnemonic(data,addr):
    if len(data)<4:return None
    items=list(md.disasm(data[:4],addr,count=1))
    return (items[0].mnemonic+" "+items[0].op_str).strip() if items else None


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--old",type=Path,required=True)
    p.add_argument("--new",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    old=modules(args.old)
    new=modules(args.new)
    assert old["eg"]["sha256"]==BASELINE_SHA
    eg_old=old["eg"]["_payload"]
    eg_new=new["eg"]["_payload"]
    assert len(eg_old)==len(eg_new)==81807709
    report={
      "status":"static-only-not-function-verified",
      "eg_3_11_sha":old["eg"]["sha256"],
      "eg_3_12_sha":new["eg"]["sha256"],
      "provisional_load_base":hex(BASE),
      "known_qemu_3_11_sites":{},
      "li_exact_byte_diff":[],
      "sparse_instruction_word_candidates":[],
      "limitations":[
        "QEMU C3.11 address locations do not prove the same function is at that C3.12 address",
        "AArch64 disassembly of arbitrary data can produce plausible-looking instructions",
        "No executed call chain, symbol boundary, or lens fix has yet been proven",
      ],
    }
    for name,pc in KNOWN_SITES.items():
        i=pc-BASE
        a=eg_old[i:i+64]
        b=eg_new[i:i+64]
        report["known_qemu_3_11_sites"][name]={
          "c3_11_runtime_pc":hex(pc),
          "eg_relative_offset":hex(i),
          "same_64_bytes":a==b,
          "different_bytes_in_64":sum(x!=y for x,y in zip(a,b)),
          "first_4_byte_instruction_old":mnemonic(a,pc),
          "first_4_byte_instruction_new":mnemonic(b,pc),
        }

    li_a=old["li"]["_payload"]
    li_b=new["li"]["_payload"]
    assert len(li_a)==len(li_b)
    report["li_exact_byte_diff"]=[
      {"relative_offset":hex(i),"old_byte":hex(a),"new_byte":hex(b)}
      for i,(a,b) in enumerate(zip(li_a,li_b)) if a!=b
    ]

    candidates=[]
    for pstart in range(0,len(eg_old),4096):
        oldpage=eg_old[pstart:pstart+4096]
        newpage=eg_new[pstart:pstart+4096]
        if oldpage==newpage:continue
        changed=sum(a!=b for a,b in zip(oldpage,newpage))
        if not 1<=changed<=24:continue
        changed_words=set()
        for ix,(a,b) in enumerate(zip(oldpage,newpage)):
            if a!=b:changed_words.add((pstart+ix)//4*4)
        if len(changed_words)>8:continue
        for off in sorted(changed_words):
            before=mnemonic(eg_old[off:off+4],BASE+off)
            after=mnemonic(eg_new[off:off+4],BASE+off)
            if before is None or after is None:continue
            mb=before.split(" ",1)[0]
            ma=after.split(" ",1)[0]
            priority=3 if mb in BRANCH or ma in BRANCH else (1 if mb!=ma else 0)
            candidates.append({"eg_offset":hex(off),"provisional_runtime_pc":hex(BASE+off),
                               "page_changed_bytes":changed,
                               "old_instruction":before,"new_instruction":after,
                               "priority":priority,"unverified_code_site":True})
    candidates.sort(key=lambda x:(-x["priority"],x["page_changed_bytes"],int(x["eg_offset"],16)))
    report["sparse_instruction_word_candidates"]=candidates[:70]
    report["all_sparse_decodable_instruction_candidates"]=len(candidates)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"arm64_triage.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    lines=["# Z8 C3.12 AArch64 static triage","",
       "All source containers passed module/package CRC verification before this analysis.",
       "Known sites are addresses from the **C3.11** QEMU boot harness; their C3.12 identity is unverified.","",
       "| C3.11 site | Old address | 64 bytes unchanged? | Different bytes |",
       "| --- | --- | --- | ---: |"]
    for name,item in report["known_qemu_3_11_sites"].items():
        lines.append(f'| {name} | `{item["c3_11_runtime_pc"]}` | {item["same_64_bytes"]} | {item["different_bytes_in_64"]} |')
    lines += ["", "Linux LI exact byte differences: **"+str(len(report["li_exact_byte_diff"]))+"**.","",
              "Sparse candidates with valid-looking AArch64 words: **"+str(len(candidates))+"** (only the first 70 are listed in JSON).",
              "", "**These are not verified function boundaries or an identified lens-fix call path.**",
              ""]
    (args.out/"arm64_triage.md").write_text("\n".join(lines))
    print(json.dumps({"li_changed_bytes":report["li_exact_byte_diff"],
                      "known_sites_changed":sum(not x["same_64_bytes"] for x in report["known_qemu_3_11_sites"].values()),
                      "sparse_candidates":len(candidates)},indent=2))


if __name__=="__main__":
    main()
