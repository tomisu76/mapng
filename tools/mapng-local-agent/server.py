from __future__ import annotations

import argparse
import json
import os
import shutil
import threading
import time
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / ".mapng-agent"
MAPS = RUNTIME / "maps"
COMMANDS = RUNTIME / "commands"
RESULTS = RUNTIME / "results"

for directory in (RUNTIME, MAPS, COMMANDS, RESULTS):
    directory.mkdir(parents=True, exist_ok=True)


class Handler(SimpleHTTPRequestHandler):
    server_version = "MapNGAgent/0.1"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def _json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({"ok": True, "service": "mapng-local-agent", "version": "0.1.0", "root": str(ROOT)})
            return
        if path == "/api/maps":
            maps = [{"name": p.name, "bytes": p.stat().st_size, "modified": p.stat().st_mtime} for p in sorted(MAPS.glob("*.zip"))]
            self._json({"maps": maps})
            return
        if path == "/api/commands":
            items = []
            for p in sorted(COMMANDS.glob("*.json")):
                try:
                    items.append(json.loads(p.read_text(encoding="utf-8")))
                except Exception:
                    items.append({"id": p.stem, "error": "invalid json"})
            self._json({"commands": items})
            return
        if path.startswith("/maps/"):
            name = Path(path).name
            target = MAPS / name
            if not target.exists() or target.suffix.lower() != ".zip":
                self.send_error(404)
                return
            self.path = "/.mapng-agent/maps/" + name
            return super().do_GET()
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/beamng-viewer/")
            self.end_headers()
            return
        return super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/maps/upload":
            filename = Path(self.headers.get("X-Filename", "map.zip")).name
            if not filename.lower().endswith(".zip"):
                self._json({"ok": False, "error": "only ZIP files are accepted"}, 400)
                return
            target = MAPS / filename
            temporary = target.with_suffix(target.suffix + ".part")
            temporary.write_bytes(self._body())
            os.replace(temporary, target)
            self._json({"ok": True, "name": filename, "bytes": target.stat().st_size}, 201)
            return
        if path == "/api/commands":
            try:
                command = json.loads(self._body().decode("utf-8"))
            except Exception as exc:
                self._json({"ok": False, "error": f"invalid JSON: {exc}"}, 400)
                return
            command_id = command.get("id") or str(uuid.uuid4())
            envelope = {"id": command_id, "createdAt": time.time(), "status": "queued", "command": command}
            target = COMMANDS / f"{command_id}.json"
            target.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
            self._json(envelope, 202)
            return
        self.send_error(404)


def main() -> None:
    parser = argparse.ArgumentParser(description="MapNG local bridge and development server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    os.chdir(ROOT / "public")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"MapNG Local Agent: http://{args.host}:{args.port}")
    print(f"Health: http://{args.host}:{args.port}/api/health")
    print(f"Runtime: {RUNTIME}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
