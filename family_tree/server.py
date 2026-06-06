import json
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from .engine import FamilyTree

PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class FamilyTreeHandler(SimpleHTTPRequestHandler):
    tree = None

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message, status=400):
        self._send_json({"error": message}, status)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw)

    def _parse_path(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path, qs = self._parse_path()

        if path == "/api/people":
            data = []
            for pid in sorted(self.tree.people):
                p = self.tree.people[pid]
                parents = self.tree.get_parents(pid)
                children = self.tree.get_children(pid)
                siblings = self.tree.get_siblings(pid)
                data.append({
                    "id": pid,
                    "name": p.get("name", ""),
                    "age": p.get("age"),
                    "gender": p.get("gender", ""),
                    "bio": p.get("bio", ""),
                    "parents": parents,
                    "children": children,
                    "siblings": siblings,
                })
            self._send_json(data)

        elif path.startswith("/api/people/"):
            parts = path.split("/")
            if len(parts) == 4:
                try:
                    pid = int(parts[3])
                except ValueError:
                    self._send_error("Invalid ID")
                    return
                p = self.tree.get_person(pid)
                if not p:
                    self._send_error("Not found", 404)
                    return
                parents = self.tree.get_parents(pid)
                children = self.tree.get_children(pid)
                siblings = self.tree.get_siblings(pid)
                self._send_json({
                    "id": pid,
                    "name": p.get("name", ""),
                    "age": p.get("age"),
                    "gender": p.get("gender", ""),
                    "bio": p.get("bio", ""),
                    "relationships": p.get("relationships", []),
                    "parents": parents,
                    "children": children,
                    "siblings": siblings,
                })
            else:
                self._send_error("Invalid path")

        elif path == "/api/graph":
            nodes = []
            edges = []
            for pid, p in self.tree.people.items():
                label = p.get("name", "") or f"#{pid}"
                gender = p.get("gender", "")
                nodes.append({
                    "id": pid,
                    "label": label,
                    "title": f"#{pid}: {label}",
                    "gender": gender,
                    "age": p.get("age"),
                    "bio": p.get("bio", ""),
                })
                for rel in p.get("relationships", []):
                    edge_label = rel["type"]
                    edges.append({
                        "from": pid,
                        "to": rel["target_id"],
                        "label": edge_label,
                    })
            if not nodes:
                nodes = [{"id": 0, "label": "No people yet", "title": ""}]
            self._send_json({"nodes": nodes, "edges": edges})

        elif path.startswith("/api/relation/"):
            parts = path.split("/")
            if len(parts) == 5:
                try:
                    id1, id2 = int(parts[3]), int(parts[4])
                except ValueError:
                    self._send_error("Invalid IDs")
                    return
                try:
                    result = self.tree.get_relationship(id1, id2)
                    self._send_json({"relationship": result})
                except ValueError as e:
                    self._send_error(str(e))
            else:
                self._send_error("Invalid path")

        else:
            super().do_GET()

    def do_POST(self):
        path, _ = self._parse_path()
        body = self._read_body()

        if path == "/api/people":
            pid = self.tree.add_person(
                name=body.get("name", ""),
                age=body.get("age"),
                gender=body.get("gender", ""),
                bio=body.get("bio", ""),
            )
            self.tree.save()
            self._send_json({"id": pid}, 201)

        elif path == "/api/relations":
            pid = body.get("person_id")
            target_id = body.get("target_id")
            rel_type = body.get("type")
            if not all([pid, target_id, rel_type]):
                self._send_error("Missing fields: person_id, target_id, type")
                return
            try:
                self.tree.add_relationship(pid, target_id, rel_type)
                self.tree.save()
                self._send_json({"status": "ok"})
            except ValueError as e:
                self._send_error(str(e))

        else:
            self._send_error("Not found", 404)

    def do_DELETE(self):
        path, qs = self._parse_path()

        if path.startswith("/api/people/"):
            parts = path.split("/")
            if len(parts) == 4:
                try:
                    pid = int(parts[3])
                except ValueError:
                    self._send_error("Invalid ID")
                    return
                try:
                    self.tree.delete_person(pid)
                    self.tree.save()
                    self._send_json({"status": "ok"})
                except ValueError as e:
                    self._send_error(str(e))
            else:
                self._send_error("Invalid path")

        elif path == "/api/relations":
            body = self._read_body()
            pid = body.get("person_id")
            target_id = body.get("target_id")
            rel_type = body.get("type")
            if not all([pid, target_id, rel_type]):
                self._send_error("Missing fields")
                return
            try:
                self.tree.delete_relationship(pid, target_id, rel_type)
                self.tree.save()
                self._send_json({"status": "ok"})
            except ValueError as e:
                self._send_error(str(e))

        else:
            self._send_error("Not found", 404)

    def do_PUT(self):
        path, _ = self._parse_path()
        body = self._read_body()

        if path.startswith("/api/people/"):
            parts = path.split("/")
            if len(parts) == 4:
                try:
                    pid = int(parts[3])
                except ValueError:
                    self._send_error("Invalid ID")
                    return
                try:
                    self.tree.update_person(
                        pid,
                        name=body.get("name"),
                        age=body.get("age"),
                        gender=body.get("gender"),
                        bio=body.get("bio"),
                    )
                    self.tree.save()
                    self._send_json({"status": "ok"})
                except ValueError as e:
                    self._send_error(str(e))
            else:
                self._send_error("Invalid path")
        else:
            self._send_error("Not found", 404)


def serve(tree, port=PORT):
    FamilyTreeHandler.tree = tree
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.chdir(static_dir)
    server = HTTPServer(("", port), FamilyTreeHandler)
    print(f"Family Tree web UI running at http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()
