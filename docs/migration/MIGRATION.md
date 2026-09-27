# Research grammar v1 migration ledger

This bootstrap migration replaced the seed ontology without a compatibility layer. The mapping below is audit documentation only; it is not canonical research state.

## Concept mapping

| Previous concept | Universal model concept |
|---|---|
| Exploration | Study |
| Probe | Method |
| Evidence | No direct object; grounded outcomes become Results and evidential roles are expressed by scholarly Relations |
| Insight | Claim with `claim_type: interpretation` or `definition`, according to meaning |

Question and Claim remain, but every seed object received a new ID. Claim field `proposition` became `statement`, and all migrated seed Claims use `claim_type: proposition`. Source and Relation remain internal canonical concepts with new `SRC` and `REL` IDs and the human-facing names Reference and Connection. Runs now use `study_id` and `method_id`.

## Seed object mapping

### Questions

| Previous ID | New ID |
|---|---|
| `DAWN-Q-01M31BQ4QWZ8CDF6G0PGEXZ6Z2` | `DAWN-Q-01M3E4R071NBX7X2KYEJ9CTKHC` |
| `DAWN-Q-01M31BQ4QW8D5NDHR8NWBMVM1A` | `DAWN-Q-01M3E4R0711K5EGJS19FWGHC54` |
| `DAWN-Q-01M31BQ4QW2W3JS1514QYN0YKT` | `DAWN-Q-01M3E4R071ZMR0JDTCXZB7530Q` |
| `DAWN-Q-01M31BQ4QWHN4TCGEFYA1XA494` | `DAWN-Q-01M3E4R071CQJ5ZB1XKVFQE9ZY` |
| `DAWN-Q-01M31BQ4QWRD6ZKXVRRJ6P0ANQ` | `DAWN-Q-01M3E4R071G8D3Q39AZQJN7TX4` |
| `DAWN-Q-01M31BQ4QWX2MB9G5Y5QYCQV61` | `DAWN-Q-01M3E4R0714580E2PH6MQV64ZW` |
| `DAWN-Q-01M31BQ4QWAW76FGWYYGP8X7HM` | `DAWN-Q-01M3E4R0711NK2MK0ZJGES3XRW` |

### Claims

| Previous ID | New ID |
|---|---|
| `DAWN-C-01M31BQ4QW2KGX8YH1QSWK6C6D` | `DAWN-C-01M3E4R071SDT4VJ3JGB6S8NE1` |
| `DAWN-C-01M31BQ4QW83D0XDDNM53214V6` | `DAWN-C-01M3E4R071ZC8EESMDFX0GHPJT` |
| `DAWN-C-01M31BQ4QWNMDE3PC6H09YE7PZ` | `DAWN-C-01M3E4R071RM1E88PC4DNSRRDE` |
| `DAWN-C-01M31BQ4QWSQKX8Y2HH18SPX4B` | `DAWN-C-01M3E4R071GJ56JWFJEXJVQ3F1` |

### Probes to Methods

| Previous ID | New ID |
|---|---|
| `DAWN-P-01M31BQ4QW4EC7BZWTVF19Q7ME` | `DAWN-M-01M3E4R071WX2RN3HQT6J7KE01` |
| `DAWN-P-01M31BQ4QW4X7ZZM5KTRTBEAVK` | `DAWN-M-01M3E4R071TGX9GWPN7Z4ZQMB1` |
| `DAWN-P-01M31BQ4QW9DCBSESM04E8RE22` | `DAWN-M-01M3E4R07153DBQB3GE6HYWGQK` |
| `DAWN-P-01M31BREPBF76RQHY03BB6W2Z9` | `DAWN-M-01M3E4R071DTMP5AR5S9G1NGR5` |

### Explorations to Studies

| Previous ID | New ID |
|---|---|
| `DAWN-X-01M31BQ4QW05WDERXGG5181GYJ` | `DAWN-ST-01M3E4R072V5NE73SPQY5GZNHM` |
| `DAWN-X-01M31BQ4QW0JTNHDJRJNW8WN6F` | `DAWN-ST-01M3E4R072RVFWWHQWAZYR59ZX` |
| `DAWN-X-01M31BQ4QW5524B0M7CVVDVXV6` | `DAWN-ST-01M3E4R072CEAYSMS6T1AV9MZY` |
| `DAWN-X-01M31BQ4QWGBRV7PR81SKM6DQZ` | `DAWN-ST-01M3E4R072TTGAGNX0F2DGAQ72` |
| `DAWN-X-01M31BQ4QWTJHYYGY4RVNX31QB` | `DAWN-ST-01M3E4R0728ASN87HMWZ4BG7YX` |
| `DAWN-X-01M31BQ4QWVSS8HHD2F853X4QT` | `DAWN-ST-01M3E4R072GR45VJ05KXCRXS04` |
| `DAWN-X-01M31BQ4QWY056GC1H58WEJRY6` | `DAWN-ST-01M3E4R072JTK7TK826BPZZ098` |

### Reference and Connections

| Previous ID | New ID |
|---|---|
| `DAWN-S-01M31BQ4QWFGVD7Z2P679X2Y7X` | `DAWN-SRC-01M3E4R0715G79XJN8DBEF6APX` |
| `DAWN-R-01M31BQ4QW2VGJVY8M7N9QVMCM` | `DAWN-REL-01M3E4R071JK3JS8S5VE6GPPD0` |
| `DAWN-R-01M31BQ4QW4SD49JC1BJ24KTED` | `DAWN-REL-01M3E4R071X7PEKPKS7T1TNNFG` |
| `DAWN-R-01M31BQ4QWAP3K58XFDXR7X02Y` | `DAWN-REL-01M3E4R071ZPYBKDCCP9WXC5NC` |
| `DAWN-R-01M31BQ4QWHK4JT3Z711T0GQXS` | `DAWN-REL-01M3E4R0712NEDHEKA5P2WK0NY` |
| `DAWN-R-01M31BQ4QWQ2M9ZPKX57Q4J502` | `DAWN-REL-01M3E4R071KQN2RV31GP9AQM4V` |
| `DAWN-R-01M31BQ4QWSHK5YF8AVF96HTYQ` | `DAWN-REL-01M3E4R072VYCC7G0ZAZBZ9TKN` |
| `DAWN-R-01M31BQ4QWTVZQNF34BDNV5SH4` | `DAWN-REL-01M3E4R072RQNGK0SNJXK7X2PD` |
| `DAWN-R-01M31BQ4QWXGBA3A2PFFA4M3QC` | `DAWN-REL-01M3E4R072EPCDSJ2DVXWSCFEC` |

The two previous Question-to-Claim `motivates` edges were normalized to Claim-to-Question `answers` Connections. The two Method-to-Question edges use `investigates`; Method-to-Claim edges use `tests`; the checked evaluator Source `motivates` the reference-checkpoint Question. No historical intellectual provenance was inferred. Execution bookkeeping edges were not retained.

## Migration outcome

The verified pre-migration inventory was 7 Questions, 4 Claims, 0 Insights, 4 Probes, 0 Evidence records, 7 Explorations, 1 Source, 8 Relations, and 0 Runs. The final seed inventory is 7 open Questions, 4 proposed Claims, 4 Methods, 7 Studies, 0 Results, 1 Source/Reference, 8 proposed Relations/Connections, 1 Artifact, and 0 Runs.

The legacy language-behavior Exploration maps to one Study containing distinct zero-shot and autoregressive-generation Methods and Method-specific execution plans. Only the zero-shot plan has a supported entrypoint. Studies that lack a sufficiently specified Method retain their missing-capability intent in completion criteria and blockers rather than receiving a fabricated Method or executable plan.

An intermediate bootstrap branch had split language generation into an eighth Study and still used one Study-wide entrypoint. That shape was not retained. The final model separates semantic Study references from `execution.plans`, supports multiple Methods, and fails closed when executable Method selection is ambiguous.

No Insight or Evidence seed object existed, and none was synthesized. No Result, Run, supported Claim, interpretation or definition Claim, accepted Connection, review, or provenance assertion was fabricated.

DAWN-SRW code was not copied or modified. The program still references the separately MIT-licensed repository at commit `30165201e68897d75f0586805d321393159550c3`; this repository remains Apache-2.0 licensed.
