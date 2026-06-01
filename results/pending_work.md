# Pending Work Notes

## Geospatial Data Completion (from failure-probability module)

- Current `formal_guangdong_2024` coordinates are mapped from CIGRE local diagram geometry.
- These coordinates are suitable for method verification, but not real Guangdong utility GIS locations.
- Next step is to replace mapped coordinates with real line/tower/substation geodata.

## Recommended Follow-up

- Ingest OSM/Geofabrik Guangdong power-layer data (line/tower/substation).
- Build a topology-matching step to map OSM assets to the 15-bus/15-line study grid.
- Re-run:
  - `scripts/component_failure_probability.py`
  - `scripts/spatiotemporal_contingency_generator.py`
- Compare key metrics before and after real-geo replacement:
  - vulnerable-line ranking stability
  - high-risk scenario coverage
  - disconnected-load statistics

