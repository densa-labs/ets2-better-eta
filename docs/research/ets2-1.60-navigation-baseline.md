# ETS2 1.60 Navigation Baseline

## Environment and provenance

- Target: Euro Truck Simulator 2 1.60; exact build is not yet known.
- Inspection date: 2026-09-14.
- Input source: no legitimately supplied ETS2 archives, extracted definition tree, or `def/map_data.sii` was present in the remote workspace.
- Direct data availability: missing.
- Inspected file hashes: unavailable until authoritative input is supplied.

This document deliberately contains no reconstructed or historical stock values. Official public documentation can help interpret fields, but cannot establish the exact values shipped in ETS2 1.60.

### Expected local input

Raw proprietary game data is development input, not repository source. Place legitimately extracted data under the ignored path:

```text
.local/
└── ets2/
    └── 1.60/
        └── def/
            ├── map_data.sii
            └── ...every local file reachable through @include
```

The smallest useful input is extracted ETS2 1.60 `def/map_data.sii` plus every local `@include` file it references. A locally owned complete `def.scs` is also acceptable later in an environment with appropriate official extraction tooling; the archive must not be committed.

Run the dependency-free inspector with Python 3:

```sh
python3 tools/inspect_navigation_baseline.py .local/ets2/1.60
```

It accepts either the extracted root or a direct path to `map_data.sii`. It hashes every reachable inspected file, inventories `navigation*` and `navigation_time_*` assignments without numeric conversion, and reports includes, missing targets, cycles, expected fields, and unexpected time fields. Its report is deterministic for a fixed input at a fixed path.

## Definition topology

Known target entry point:

```text
def/map_data.sii
└── @include topology: unknown until authoritative data is supplied
```

Smallest candidate override boundary: unknown. No current file was available to determine whether the navigation definitions are monolithic or split into a narrower include.

## Full current navigation-field inventory

Not verified. Authoritative ETS2 1.60 data was not available. No historical documentation, schema defaults, ATS data, community mod values, web snippets, or remembered values have been substituted.

## Direct Better ETA candidate fields

| Exact field spelling | Exact ETS2 1.60 value | Source | Status |
|---|---:|---|---|
| `navigation_time_narrow_road_max_speed_usage` | — | — | missing authoritative input |
| `navigation_time_road_max_speed_usage` | — | — | missing authoritative input |
| `navigation_time_city_or_slowtime_speed_penalty` | — | — | missing authoritative input |
| `navigation_time_semaphore_wait_duration` | — | — | missing authoritative input |
| `navigation_time_stop_wait_duration` | — | — | missing authoritative input |
| `navigation_time_turn_own_side_duration` | — | — | missing authoritative input |
| `navigation_time_turn_oposite_side_duration` | — | — | missing authoritative input |

The spelling `oposite` is intentional and must remain exact.

## Additional findings

- Additional `navigation_time_*` fields: unknown.
- Unexpected routing or obsolete-looking fields: unknown.
- Include structure and definition ownership: unknown.
- Hypothesis: a narrower include may exist, but this is unverified and must not guide package design until current data is inspected.

No values have been changed, no production mod has been built, and no ETA accuracy claim has been made.

## Definition ownership conclusion

**C. Insufficient data to decide.**

The actual ETS2 1.60 `def/map_data.sii` and its reachable includes are required to decide whether Better ETA can own a narrower navigation include or must override the full definition.

## Milestone status

**BLOCKED ON AUTHORITATIVE ETS2 1.60 GAME DATA**

Repository bootstrap and baseline-inspection tooling can be completed and tested with synthetic fixtures, but the authoritative navigation baseline itself cannot be completed or used to begin Milestone 2 until the legitimate input described above is supplied.
