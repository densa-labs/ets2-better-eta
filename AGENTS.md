# Better ETA Agent Guide

## Project identity and priorities

Better ETA is a Densa Labs data-only mod for Euro Truck Simulator 2, distributed primarily through Steam Workshop. The working repository may be called `densa-labs/better-eta`; never create, rename, or push a remote unless the user explicitly requests it.

Prioritize, in order:

1. Ease of installation.
2. Measurable ETA accuracy improvement.
3. Steam Workshop compatibility.
4. Low maintenance burden.
5. Compatibility with ETS2 updates and other mods.
6. Technical elegance.

## Public product architecture

The shipped product is an ordinary data-only ETS2 mod. Its target experience is Subscribe → Enable → Play. Version 0.1 uses the smallest possible version-specific navigation-definition override, validated `navigation_time_*` changes only, stock routing, and the stock Route Advisor.

Candidate controls are:

- `navigation_time_narrow_road_max_speed_usage`
- `navigation_time_road_max_speed_usage`
- `navigation_time_city_or_slowtime_speed_penalty`
- `navigation_time_semaphore_wait_duration`
- `navigation_time_stop_wait_duration`
- `navigation_time_turn_own_side_duration`
- `navigation_time_turn_oposite_side_duration` (the game spelling is `oposite`)

Do not assume every candidate needs modification. Every non-stock value must earn its place through measured, out-of-sample ETA improvement.

Version 0.1 explicitly excludes a companion app, native runtime, Telemetry SDK plugin, IPC, installer, native overlay, personalized ML, persistent calibration profile, custom Route Advisor replacement, traffic or physics changes, economy changes, and map-sector modifications. The archived/native Adaptive ETA project is separate R&D/reference work. Do not port its runtime architecture or make it a public dependency unless the user explicitly changes direction; it may only become internal measurement instrumentation later.

## Systems left untouched by default

Do not modify navigation route-selection weights, country/legal speed limits, traffic density, AI traffic speed, traffic-light cycles, stop behaviour, truck physics, engine performance, cargo properties, weather, game time scale, `economy_data`, delivery deadlines, ferry/train actual travel duration, map sectors, prefab geometry, or Route Advisor UI.

Apply this test: does a change improve the prediction of the trip, or change the trip until the prediction appears correct? Only the former belongs in Better ETA.

## Evidence and version discipline

For current ETS2 behavior, prefer:

1. Legitimately available current shipped game data.
2. Current official SCS modding documentation.
3. Current SCS Workshop documentation and tools.
4. Official SCS developer or forum statements.
5. ATS evidence only when engine-shared and clearly labeled.
6. Maintained community technical references.
7. Controlled, reproducible experiments.

Label evidence as verified current behavior, official documented behavior, observed behavior, historical documentation, reasonable inference, or unverified hypothesis. Never silently promote historical examples, schema defaults, ATS values, community values, or memory to current stock values.

The current baseline is ETS2 1.60. Compatibility is version-specific; claim no other version until explicitly validated. For future supported versions, prefer version-specific Workshop packages over blindly reusing central definitions.

## Repository and validation rules

- Inspect the repository before implementing and preserve user files.
- Keep `README.md` concise and public-facing; do not turn it into an engineering specification or modify a human-edited README.
- Put research and implementation detail in focused documents.
- Never commit proprietary SCS archives or copied game-data trees. Derived measurements, hashes, parameter inventories, and small necessary factual excerpts are acceptable.
- Do not introduce native code without an explicit architecture change.
- Do not use Superpowers workflows.
- Do not automatically begin the next milestone.
- Do not push or alter a remote unless explicitly requested.

Always distinguish implemented, statically inspected, unit tested, locally exercised, tested in ETS2, validated through Workshop Uploader, validated on Windows, validated on Linux, and validated on macOS. Never claim live, game, or Workshop validation unless it actually occurred.
