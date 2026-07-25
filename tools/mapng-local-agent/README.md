# MapNG Studio: online viewer + local agent

This vertical slice provides two complementary runtimes.

## 1. Online BeamNG Cesium viewer

After `npm run dev` or a normal Vite deployment, open:

```text
/beamng-viewer/
```

Drop a MapNG preview ZIP containing:

```text
assets/scene.json
assets/terrain_lon_lat_height.bin
assets/terrain_st.bin
assets/terrain_indices.bin
assets/terrain.png
```

The viewer converts WGS84 longitude/latitude/height vertices directly to Cesium ECEF. It does not render the terrain through glTF, so Y-up/Z-up model rotation cannot place terrain vertically.

## 2. Local MapNG agent

Windows one-click start:

```text
tools\mapng-local-agent\START_MAPNG_AGENT.bat
```

Manual start:

```bash
python tools/mapng-local-agent/server.py
```

Default address:

```text
http://127.0.0.1:8765
```

Endpoints:

- `GET /api/health`
- `GET /api/maps`
- `POST /api/maps/upload` with raw ZIP body and `X-Filename`
- `GET /api/commands`
- `POST /api/commands` with JSON body

Runtime data is stored under `.mapng-agent/` and should not be committed.

## Intended next bridge

The command queue is deliberately transport-only. A BeamNG Lua editor extension can poll or consume validated MapNG commands and write results into `.mapng-agent/results/`. AI-generated arbitrary Lua is not accepted; commands should use a versioned schema and explicit handlers.
