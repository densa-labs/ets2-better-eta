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
| Vanilla | no data assignment | Zürich → Milan (Libellula), Motor Oil | 385 km map / 386 km Route Advisor | 5 h 36 min; Mon 22:57 → Tue 4:33 | Recorded map route through Switzerland into northern Italy | `MOD TESTING`: 0 active mods; map/navigation loaded |
| LOW | `navigation_time_road_max_speed_usage: 0.50` | Zürich → Milan (Libellula), Motor Oil | 385 km map / 386 km Route Advisor | 9 h 16 min; Mon 23:02 → Tue 8:18 | Map route visually matches Vanilla | One active local LOW mod mounted; map/navigation and route generation loaded; no unknown-attribute or duplicate-unit message observed |
| HIGH | `navigation_time_road_max_speed_usage: 1.00` | Zürich → Milan (Libellula), Motor Oil | 385 km map / 386 km Route Advisor | 5 h 08 min; Mon 22:57 → Tue 4:05 | Map route visually matches Vanilla and LOW | One active local HIGH mod mounted; map/navigation and route generation loaded; no unknown-attribute or duplicate-unit message observed |

The LOW and HIGH values are deliberately separated positive probes. They are not production recommendations and are not claims about the vanilla default.

Vanilla evidence is from the user's map and Route Advisor screenshots captured around 16:44 local time. The same ETS2 log was created at 16:40:09, recorded 0 active mods at elapsed 00:00:31, and did not mount LOW until elapsed 00:05:04 (about 16:45:14), after both screenshots. Thus the later accidental LOW activation in that log is excluded from the Vanilla observation. The map displays 385 km while the Route Advisor displays 386 km; record both rather than treating this one-kilometre display difference as a route change. The separate 20 h 11 min figure is the job deadline, not predicted travel time.

LOW evidence is from the user's map and Route Advisor screenshots captured around 16:48 local time, after the log mounted exactly one active local mod, `better_eta_m2_low`, at elapsed 00:05:04. The selected map route and both distance displays match Vanilla; the truck is shown stationary at 0 km/h. LOW's native trip-time display is 3 h 40 min longer than Vanilla's. The in-game clock advanced five minutes between screenshots, so compare predicted trip time rather than absolute arrival clock alone. The modded log contains no unknown-attribute or duplicate-unit message; it does contain map/profile warnings also seen during the Vanilla portion, which should not be silently attributed to this field assignment.

HIGH evidence is from the user's Route Advisor and map screenshots captured around 16:51 local time. The same log mounted exactly one active local mod, `better_eta_m2_high`, at elapsed 00:10:22 (about 16:50:31), before the screenshots. LOW and HIGH loaded the same manual save slot `save/3/game.sii`. Both map screenshots show the same Zürich-to-Milan red route and 385 km distance; their Route Advisors show 386 km. No extra destination or waypoint is visible. HIGH's trip-time prediction is 4 h 08 min shorter than LOW's and 28 min shorter than Vanilla's. Its in-game clock matches Vanilla at Mon 22:57, and the truck is stationary at 0 km/h.

The cumulative game log contains recurring city, ferry, DLC, and prefab warnings/errors in both the Vanilla and modded phases. A pre-existing native telemetry plugin also loaded throughout the same game session; it was not used by Better ETA and its state did not vary between conditions. Neither modded phase shows an unknown-attribute warning, duplicate-unit error, or navigation failure attributable to the experimental assignment. The game does not print a positive field-by-field acceptance message; acceptance is inferred from successful mod mount/map load and the monotonic native ETA response. The raw log and screenshots are retained only in ignored local development input, not in this repository document.

### Short live protocol

1. In Mod Manager for the disposable `MOD TESTING` profile, leave both experimental mods disabled and disable any unrelated mod that could own `def/map_data.sii`. Start from one unchanged save, set a motorway/normal-road-dominated destination, and record route geometry, distance, and initial Route Advisor travel time/ETA.
2. Return to that starting save. Enable only `Better ETA M2 - LOW 0.50`, select the identical destination/waypoints, and record the same observations plus relevant `game.log.txt` messages.
3. Repeat from that save with only `Better ETA M2 - HIGH 1.00` enabled.
4. Compare LOW to HIGH. A causal response should be monotonic: LOW predicts more travel time than HIGH while route geometry, distance, and waypoints remain unchanged.

For each modded run, confirm that the log shows the directory mod mounted and contains no unknown-attribute warning, duplicate-unit error, or serious map/navigation error caused by the test mod.

## Result

**A. `navigation_time_road_max_speed_usage` is causally active in ETS2 1.60.1.7 and can be overridden by a normal data-only mod.**

The two positive experimental assignments were activated one at a time on the same test profile and same manual save. With the selected route and distance unchanged, `0.50` predicted 9 h 16 min while `1.00` predicted 5 h 08 min. This 4 h 08 min monotonic separation in ETS2's native Route Advisor is far larger than display rounding. Vanilla lay between them at 5 h 36 min. This proves a causal response for this field on this route; it does not identify the hidden vanilla default or establish an accurate production value.

## Architecture implication

The central Better ETA v0.1 mechanism—an ordinary mod owning `def/map_data.sii` and changing a native `navigation_time_*` ETA assumption while stock routing and Route Advisor remain in use—is experimentally proven on one controlled route. The matching route geometry and distance support, but do not exhaustively prove, ETA-only behavior across all possible routes. No tuning or accuracy-improvement claim follows from this causality proof.

## Milestone status

**COMPLETE — NATIVE OVERRIDE CAUSALITY PROVEN FOR ONE FIELD AND ROUTE**
