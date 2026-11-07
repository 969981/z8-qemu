# Z8 C3.12 static breakpoint relocation candidates

All firmware modules and package CRCs verified. **No runtime equivalence verified.**
Ambiguous sites have a null candidate PC, by design.

| Site | C3.11 PC | C3.12 candidate PC | Status | Anchors |
| --- | --- | --- | --- | ---: |
| boot_entry | `0x40160000` | `0x40160000` | byte_identical | 0 |
| adc_ready | `0x4033DB98` | `0x4033db98` | byte_identical | 0 |
| power_status | `0x40D57A90` | `0x40d57a90` | two_sided_anchor_candidate | 82 |
| system_power_event | `0x40D67260` | `0x40d67260` | byte_identical | 0 |
| battery_callback | `0x41181504` | `0x4118156c` | two_sided_anchor_candidate | 54 |
| lens_controller_reply | `0x4106E690` | `0x4106e6f8` | two_sided_anchor_candidate | 70 |
| menu_event_1 | `0x40D66034` | `0x40d66034` | byte_identical | 0 |
| menu_event_2 | `0x40D55DA0` | `0x40d55da0` | two_sided_anchor_candidate | 84 |
| menu_event_3 | `0x40D5EB7C` | `0x40d5eb7c` | byte_identical | 0 |
| half_shutter_1 | `0x40D271E4` | `0x40d271e4` | two_sided_anchor_candidate | 75 |
| half_shutter_2 | `0x40D26D7C` | `0x40d26d7c` | two_sided_anchor_candidate | 95 |
| half_shutter_3 | `0x40D3003C` | `0x40d3003c` | byte_identical | 0 |
| framebuffer_event | `0x40FAC9BC` | `0x40faca24` | two_sided_anchor_candidate | 86 |
| ui_event | `0x40D57118` | `0x40d57118` | two_sided_anchor_candidate | 87 |
| gpio_rx_isr | `0x40C161F0` | `0x40c161f0` | byte_identical | 0 |
| gpio_tx_isr | `0x40C161D8` | `0x40c161d8` | byte_identical | 0 |
| rx_request | `0x40C934B4` | `0x40c934b4` | byte_identical | 0 |
| tx_request | `0x40C930EC` | `0x40c930ec` | byte_identical | 0 |
| serial_before_enable | `0x40C14A60` | `0x40c14a60` | byte_identical | 0 |
| serial_prefill | `0x40C14A8C` | `0x40c14a8c` | byte_identical | 0 |
| serial_drain | `0x40C14AD0` | `0x40c14ad0` | byte_identical | 0 |
| serial_rx_isr | `0x40C14F10` | `0x40c14f10` | byte_identical | 0 |
| rx_accepted | `0x40C935C8` | `0x40c935c8` | byte_identical | 0 |
| tx_complete | `0x40C930F0` | `0x40c930f0` | byte_identical | 0 |
| tx_ack | `0x40C931D8` | `0x40c931d8` | byte_identical | 0 |
| tx_final | `0x40C93240` | `0x40c93240` | byte_identical | 0 |

Status counts: `{'byte_identical': 18, 'two_sided_anchor_candidate': 8}`

Do not use an unvalidated address profile for capture or physical firmware changes.
