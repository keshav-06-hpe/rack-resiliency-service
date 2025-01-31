import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict
from kubernetes import client, config

PORT = 8080  # Set the port for the API

def get_zone_data():
    """Fetch and parse Kubernetes node zone information using the Kubernetes Python client"""
    try:
        # Load the in-cluster configuration
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        # Fetch node information
        nodes = v1.list_node()
        zones = defaultdict(list)

        for node in nodes.items:
            zone = node.metadata.labels.get(
                'topology.kubernetes.io/zone', 
                'unassigned'
            )
            zones[zone].append({
                'name': node.metadata.name,
                'status': node.status.conditions[-1].type if node.status.conditions else 'Unknown',
                'roles': ','.join(
                    k for k, v in node.metadata.labels.items()
                    if 'node-role.kubernetes.io/' in k
                ),
                'age': node.metadata.creation_timestamp,
                'version': node.status.node_info.kubelet_version,
                'cpu': node.status.capacity.get('cpu', 'N/A'),
                'memory': node.status.capacity.get('memory', 'N/A')
            })
        return zones
    except Exception as e:
        return {"error": str(e)}

class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler"""

    def do_GET(self):
        if self.path == "/zones":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps(get_zone_data(), indent=2)
            self.wfile.write(response.encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

def run(server_class=HTTPServer, handler_class=RequestHandler, port=PORT):
    """Run the HTTP server"""
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()