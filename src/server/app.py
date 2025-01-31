import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict

PORT = 8080

def get_zone_data():
    try:
        # Read the token from the file
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as token_file:
            token = token_file.read().strip()

        curl_command = [
            'curl', '-k',
            '-H', f"Authorization: Bearer {token}",
            'https://kubernetes.default.svc/api/v1/nodes'
        ]
        
        # Run the curl command
        result = subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        print(result)
        # Check if the command failed
        if result.returncode != 0:
            return {"error": f"Curl command failed: {result.stderr.strip()}"}

        # If response is empty
        if not result.stdout.strip():
            return {"error": "Empty response from Kubernetes API"}

        # Try parsing the JSON response
        try:
            nodes_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from Kubernetes API", "raw": result.stdout}

        zones = defaultdict(list)
        for node in nodes_data.get('items', []):
            zone = node['metadata']['labels'].get('topology.kubernetes.io/zone', 'unassigned')
            zones[zone].append({
                'name': node['metadata']['name'],
                'status': node['status']['conditions'][-1]['type'] if node['status'].get('conditions') else 'Unknown',
                'roles': ','.join(
                    k for k, v in node['metadata']['labels'].items() if 'node-role.kubernetes.io/' in k
                ),
                'age': node['metadata']['creationTimestamp'],
                'version': node['status']['nodeInfo']['kubeletVersion'],
                'cpu': node['status']['capacity'].get('cpu', 'N/A'),
                'memory': node['status']['capacity'].get('memory', 'N/A')
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