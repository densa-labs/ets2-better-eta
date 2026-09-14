# Native ETA Override Proof

## Baseline

- Game: Euro Truck Simulator 2 `1.60.1.7s`, revision `26c95e307fd5`, Steam build `23966373`.
- Installed `def.scs` SHA-256: `d79ac4944bbbb810d3f81f390b9fbea0fc4eeb9845b4de2c616d28b151e46076`.
- Stock `def/map_data.sii` SHA-256: `9433ef7c8d120509ee641f6d1643966ddc99effe1f237ec9c6b34025bdb72473`.
- Stock assignment of `navigation_time_road_max_speed_usage`: none. Its effective internal default is unknown.

The experiment uses an ordinary directory mod containing a generated full `def/map_data.sii`. The generated file is the verified stock file with one surgical insertion; no routing weight or other game value is changed.

## Prepared development artifacts

Materialize either condition from the ignored authoritative input:

```console
python3 tools/materialize_dev_mod.py .local/ets2/1.60/def/map_data.sii experiments/road-speed-usage/low.json
python3 tools/materialize_dev_mod.py .local/ets2/1.60/def/map_data.sii experiments/road-speed-usage/high.json
```

The generated directory mods are ignored under `build/dev-mod/`. They were also copied to the normal macOS ETS2 user mod directory as `better_eta_m2_low` and `better_eta_m2_high`; the installed game and `def.scs` were not modified.

| Profile | Inserted value | Generated `map_data.sii` SHA-256 |
|---|---:|---|
| LOW | `0.50` | `00f3793d3c2147d157e16a394ea771ae7c67c7183c8abeebe5aa4f09c9bac54b` |
| HIGH | `1.00` | `6dbfb4cdb50ff229870c7e1413fee9e6cc392e3ccbc161be4365208f725b8693` |

Inspection confirmed that each output contains its assignment exactly once and otherwise differs from the stock source only by the experimental comment and assignment. Repeated materialization produced the same hashes.

## Experiment

Use the disposable local profile `MOD TESTING`. Keep the truck, starting save, route preference, destination/waypoints, and selected route identical. Record the native Route Advisor values before driving.

| Condition | Explicit field/value | Route | Distance | Travel time / ETA | Route identity | Game-log status |
|---|---|---|---:|---|---|---|
| Vanilla | no data assignment | not observed | not observed | not observed | not observed | not run |
| LOW | `navigation_time_road_max_speed_usage: 0.50` | not observed | not observed | not observed | not observed | not enabled |
| HIGH | `navigation_time_road_max_speed_usage: 1.00` | not observed | not observed | not observed | not observed | not enabled |

The LOW and HIGH values are deliberately separated positive probes. They are not production recommendations and are not claims about the vanilla default.

### Short live protocol

1. In Mod Manager for the disposable `MOD TESTING` profile, leave both experimental mods disabled and disable any unrelated mod that could own `def/map_data.sii`. Start from one unchanged save, set a motorway/normal-road-dominated destination, and record route geometry, distance, and initial Route Advisor travel time/ETA.
2. Return to that starting save. Enable only `Better ETA M2 - LOW 0.50`, select the identical destination/waypoints, and record the same observations plus relevant `game.log.txt` messages.
3. Repeat from that save with only `Better ETA M2 - HIGH 1.00` enabled.
4. Compare LOW to HIGH. A causal response should be monotonic: LOW predicts more travel time than HIGH while route geometry, distance, and waypoints remain unchanged.

For each modded run, confirm that the log shows the directory mod mounted and contains no unknown-attribute warning, duplicate-unit error, or serious map/navigation error caused by the test mod.

## Result

**D. Live validation could not yet be completed.**

After correcting the generated manifest's SII unit identifier, a fresh `1.60.1.7s` launch discovered both local directory packages without manifest parsing errors. However, the available automated desktop input could not reliably activate Mod Manager controls in ETS2. Neither experiment was enabled, so `map_data.sii` was not parsed from the test mod and field acceptance, ETA response, and route isolation remain unverified. Prepared artifacts and package discovery do not prove the native mechanism. Replace this result only with direct observed evidence.

## Architecture implication

The central Better ETA mechanism is not yet experimentally proven. Do not begin tuning or infer the hidden vanilla default until the live LOW/HIGH comparison succeeds.

## Milestone status

**INCOMPLETE — LIVE CAUSAL VALIDATION PENDING**
