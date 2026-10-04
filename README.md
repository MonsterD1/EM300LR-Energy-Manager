# B-Control EM300 LR Energy Manager

Home Assistant integration for the **B-Control / TQ EM300 LR** energy manager.
Reads all OBIS values from the device's local web service in one request per interval.

- Local polling, no cloud
- One request per interval; the session is reused and renewed only when the device reports it expired
- Setup via UI (host, optional password), interval adjustable in the options (default 60 s)
- Only grid import/export power and energy are enabled by default; all other values (L1–L3, reactive, apparent, power factor, frequency, current, voltage) are created **disabled** and can be enabled per entity

## Installation (HACS)

1. HACS → ⋮ → *Custom repositories* → `https://github.com/MonsterD1/EM300LR-Energy-Manager`, category *Integration*
2. Install **B-Control EM300 LR Energy Manager**, restart Home Assistant
3. *Settings → Devices & services → Add integration → B-Control EM300 LR*, enter the IP address

## Entities

Device name `BControlEM300`, so entity IDs are `sensor.bcontrolem300_<name>`:

| OBIS | Entity | Default |
|---|---|---|
| 1-0:1.4.0 | `active_power_plus` (grid import, W) | enabled |
| 1-0:2.4.0 | `active_power_minus` (grid export, W) | enabled |
| 1-0:1.8.0 | `active_energy_plus` (import counter, Wh) | enabled |
| 1-0:2.8.0 | `active_energy_minus` (export counter, Wh) | enabled |
| 1-0:3/4.x, 9/10.x | reactive / apparent power and energy | disabled |
| 1-0:13.4 / 14.4 | power factor / frequency | disabled |
| 1-0:21–33, 41–53, 61–73 | per phase L1/L2/L3: power, energy, current, voltage, power factor | disabled |

## Migrating from the command_line + template setup

The entity IDs match the common `command_line` script + template sensor setup
(`sensor.bcontrolem300_*`), so history and long-term statistics continue:

1. Remove the `bcontrol_em300_data` command_line sensor and the `BControlEM300 …` template sensors, restart
2. Delete the leftover (orphaned) `sensor.bcontrolem300_*` entities under *Settings → Entities*
3. Add this integration – the entities get the old IDs back

## Protocol

```
GET  /start.php                -> session cookie, {"serial", "auth_mode", "authentication"}
POST /start.php login=<serial>&password=<pw>   (only if authentication is false)
GET  /mum-webservice/data.php  -> all OBIS values, or {"authentication": false} when the session expired
```
