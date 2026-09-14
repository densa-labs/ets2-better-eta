# ETS2 1.60 Navigation Baseline

## Installed source and provenance

- Game: Euro Truck Simulator 2 `1.60.1.7s`, revision `26c95e307fd5`.
- Steam app ID: `227300`.
- Steam build ID: `23966373`.
- macOS app metadata: short version `1.60.0`, bundle build `78988`.
- Pack metadata: `version.scs` reports application `eut2`, version `1.60.1.7`, and creation timestamp `1782738046`.
- Source: the user's legitimate Steam installation in the standard primary macOS Steam library.
- Inspection date: 2026-09-15.
- Extraction: `Archive::SCS` 1.12 on Perl 5.34.1, reading the installed HashFS v2 `def.scs`; extracted development input remains under ignored `.local/ets2/1.60/`.

Version evidence is mutually consistent: `version.scs`, the game-generated log, the game executable's startup banner, Steam's app manifest, and the app bundle all identify the installation as the stable 1.60 line. The most precise local version is `1.60.1.7s` revision `26c95e307fd5`.

### SHA-256 provenance

| Installed or extracted artifact | SHA-256 |
|---|---|
| Installed `def.scs` | `d79ac4944bbbb810d3f81f390b9fbea0fc4eeb9845b4de2c616d28b151e46076` |
| Installed `version.scs` | `a7fca9662bdbdbb106d38c695558eef6deee9560c5af358582cccfd8dc5dd4e1` |
| Installed macOS game executable | `a3c03e9c1e0254b66e1d5cdf1439ac68675a1a37c438305a99d39b810454a430` |
| Extracted `def/map_data.sii` | `9433ef7c8d120509ee641f6d1643966ddc99effe1f237ec9c6b34025bdb72473` |

The game log also reports that `def.scs` was mounted and validated with 66,928 archive entries. A complete local extraction produced 64,629 files (61,569 `.sii` files); the difference includes directory index entries. A full-tree text search of that extracted definition tree found no `navigation_time_` assignment.

Raw archives and extracted files are proprietary development inputs. They are ignored and must not be committed. Only the derived inventory and hashes below belong in the repository.

## Definition topology

The actual topology is monolithic:

```text
def.scs
└── def/map_data.sii
    └── map_data : .map.data { ... }
        └── no @include directives
```

`def/map_data.sii` is 5,456 bytes and 157 lines. It contains no textual `@include` relationship, navigation-specific or otherwise. The archive has no separate navigation definition file associated with this unit.

## Verified navigation inventory

The inspector found every assignment beginning with `navigation` in the authoritative `def/map_data.sii`:

| Field | Exact assigned value | Classification | Source |
|---|---:|---|---|
| `navigation_color` | `0xFF0C0CCF` | Route Advisor presentation | `def/map_data.sii:22` |
| `navigation_highlight_color` | `0xFF0C42DF` | Route Advisor presentation | `def/map_data.sii:23` |
| `navigation_fade_color` | `0xFF07077C` | Route Advisor presentation | `def/map_data.sii:24` |
| `navigation_arrow_color` | `0xFF06FB11` | Route Advisor presentation | `def/map_data.sii:25` |
| `navigation_city_penalty` | `3.0` | route-selection penalty | `def/map_data.sii:153` |
| `navigation_slow_road_penalty` | `5.0` | route-selection penalty | `def/map_data.sii:154` |

The two assigned penalty fields are adjacent routing controls, not direct time-evaluation fields. Better ETA leaves them unchanged by default. The four color fields are unrelated presentation controls.

One additional assignment beginning with `navigation` exists elsewhere in `def.scs`: `navigation_bar_screens: "/ui/!desc_navigation_bar.sii"` in `def/desktop_screen_config.sii`. It configures desktop UI and is unrelated to route time evaluation.

## Better ETA candidate controls

All seven candidate names occur verbatim in the shipped 1.60.1.7 game executable, which verifies current engine recognition. None is assigned in `def/map_data.sii`, in a reachable include (there are none), or anywhere else in the complete extracted `def.scs` tree.

| Exact field spelling | Exact assigned 1.60.1.7 stock value | Source definition | Verification status |
|---|---|---|---|
| `navigation_time_narrow_road_max_speed_usage` | not assigned | none | verified absent from shipped definitions |
| `navigation_time_road_max_speed_usage` | not assigned | none | verified absent from shipped definitions |
| `navigation_time_city_or_slowtime_speed_penalty` | not assigned | none | verified absent from shipped definitions |
| `navigation_time_semaphore_wait_duration` | not assigned | none | verified absent from shipped definitions |
| `navigation_time_stop_wait_duration` | not assigned | none | verified absent from shipped definitions |
| `navigation_time_turn_own_side_duration` | not assigned | none | verified absent from shipped definitions |
| `navigation_time_turn_oposite_side_duration` | not assigned | none | verified absent from shipped definitions |

The spelling `oposite` is verified and intentional.

This finding does **not** establish that the effective numeric value is zero. It establishes that ETS2 1.60.1.7 supplies no textual numeric value for these members in its shipped definitions. Any effective values come from internal defaults or other runtime behavior. Historical documentation, generated schema defaults, ATS values, community mod values, and memory remain inadmissible substitutes for exact current assigned values.

## Additional current fields

There are no additional `navigation_time_*` assignments in the extracted definition tree.

The shipped executable also contains the following related names. These strings verify that the current binary recognizes or references the names, but do not establish semantics, use, or numeric values:

- Parallel routing controls: `navigation_narrow_road_max_speed_usage`, `navigation_road_max_speed_usage`, `navigation_city_or_slowtime_speed_penalty`, `navigation_semaphore_wait_duration`, `navigation_stop_wait_duration`, `navigation_turn_own_side_duration`, and `navigation_turn_oposite_side_duration`.
- Other navigation/routing names: `navigation_bus_maximum_speed`, `navigation_car_maximum_speed`, `navigation_maximum_speed`, `navigation_gps_avoid_additive_penalty`, `navigation_prefer_small_wide_road_penalty`, `navigation_prohibited_vehicle_type_penalty`, `navigation_roundabout_penalty`, `navigation_special_prefab_additive_penalty`, `navigation_special_prefab_additive_penalty_city`, `navigation_turn_back_length`, and `navigation_turn_back_limit`.

None of these binary-observed names is automatically part of Better ETA's tuning surface. In particular, the parallel non-`time` controls remain route-selection controls and are out of scope by default.

## Definition ownership conclusion

**B. Better ETA needs to own full `def/map_data.sii`.**

Evidence:

1. The installed `def/map_data.sii` defines the single `.map.data` unit directly.
2. It contains no `@include` directives.
3. There is no navigation-specific child definition to override more narrowly.
4. Therefore, an ordinary data mod that assigns recognized members on `.map.data` would need to replace the full `def/map_data.sii` ownership point.

This is a definition-ownership conclusion only. It does not authorize adding any candidate field, selecting a value, building the production package, or claiming that an override improves ETA. Because the seven fields are unassigned in stock data, a later milestone must explicitly address how proposed values can be justified against unknown effective internal defaults before tuning begins.

## Milestone status

**COMPLETE**

The authoritative ETS2 1.60 navigation-definition baseline is established for the locally installed stable build `1.60.1.7s`. The seven candidate fields are verified as engine-recognized but not explicitly assigned in the shipped definitions, there are no additional `navigation_time_*` assignments, the topology is monolithic, and full `def/map_data.sii` ownership would be required. Milestone 2 has not begun.
