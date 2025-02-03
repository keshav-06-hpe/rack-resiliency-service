import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict

PORT = 8080

def read_token():
    """
    Reads the Kubernetes service account token from the default location.

    Returns:
        str: The token as a string.
    """
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as token_file:
            return token_file.read().strip()
    except Exception as e:
        raise Exception(f"Failed to read token: {str(e)}")

def get_zone_data():
    """
    Fetches zone data from the Kubernetes API.

    Returns:
        dict: A dictionary containing zone data or an error message.
    """
    try:
        token = read_token()
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

def get_critical_pods():
    """
    Fetches critical pods (services) data from the Kubernetes API across all namespaces.

    Returns:
        dict: A dictionary containing critical pods data or an error message.
    """
    try:
        token = read_token()
        # Define the list of critical pods (services)
        critical_pods = {
            "K8s Control Plane Services": {
                "kube-apiserver": [],
                "kube-scheduler": [],
                "kube-controller-manager": [],
                "kube-proxy": [],
                "coredns": []
            },
            "Networking": {
                "slingshot-fabric-manager": []
            },
            "Work Load Manager": {
                "pbs": [],
                "slurm": []
            },
            "iscsi": [],
            "ceph": [],
            "etcd": [],
            "postgres": [],
            "nexus": [],
            "cray-hbtd": []
        }

        # Fetch pods from all namespaces
        curl_command = [
            'curl', '-k',
            '-H', f"Authorization: Bearer {token}",
            'https://kubernetes.default.svc/api/v1/pods'
        ]

        # Run the curl command
        result = subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # Check if the command failed
        if result.returncode != 0:
            return {"error": f"Curl command failed: {result.stderr.strip()}"}

        # If response is empty
        if not result.stdout.strip():
            return {"error": "Empty response from Kubernetes API"}

        # Try parsing the JSON response
        try:
            pods_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from Kubernetes API", "raw": result.stdout}

        # Filter and categorize critical pods
        for pod in pods_data.get('items', []):
            pod_name = pod['metadata']['name']
            namespace = pod['metadata']['namespace']
            status = pod['status']['phase']
            node_name = pod['spec'].get('nodeName', 'N/A')
            creation_timestamp = pod['metadata']['creationTimestamp']

            # Check if the pod is a critical service
            for category, services in critical_pods.items():
                if isinstance(services, dict):
                    for service_name in services:
                        if service_name.lower() in pod_name.lower():
                            critical_pods[category][service_name].append({
                                'name': pod_name,
                                'namespace': namespace,
                                'status': status,
                                'node_name': node_name,
                                'creation_timestamp': creation_timestamp
                            })
                            break
                elif isinstance(services, list):
                    if category.lower() in pod_name.lower():
                        critical_pods[category].append({
                            'name': pod_name,
                            'namespace': namespace,
                            'status': status,
                            'node_name': node_name,
                            'creation_timestamp': creation_timestamp
                        })

        return critical_pods
    except Exception as e:
        return {"error": str(e)}

class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler"""
    def do_GET(self):
        """
        Handles GET requests.

        ---
        tags:
          - Zones
          - Critical Pods
        summary: Get zone data or critical pods data
        description: Returns zone data or critical pods data from the Kubernetes API.
        responses:
          200:
            description: A JSON object containing zone data or critical pods data.
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    zone_name:
                      type: array
                      items:
                        type: object
                        properties:
                          name:
                            type: string
                          status:
                            type: string
                          roles:
                            type: string
                          age:
                            type: string
                          version:
                            type: string
                          cpu:
                            type: string
                          memory:
                            type: string
                    critical_pods:
                      type: object
                      properties:
                        K8s Control Plane Services:
                          type: object
                          properties:
                            kube-apiserver:
                              type: array
                              items:
                                type: object
                                properties:
                                  name:
                                    type: string
                                  namespace:
                                    type: string
                                  status:
                                    type: string
                                  node_name:
                                    type: string
                                  creation_timestamp:
                                    type: string
                            kube-scheduler:
                              type: array
                              items:
                                type: object
                                properties:
                                  name:
                                    type: string
                                  namespace:
                                    type: string
                                  status:
                                    type: string
                                  node_name:
                                    type: string
                                  creation_timestamp:
                                    type: string
                            kube-controller-manager:
                              type: array
                              items:
                                type: object
                                properties:
                                  name:
                                    type: string
                                  namespace:
                                    type: string
                                  status:
                                    type: string
                                  node_name:
                                    type: string
                                  creation_timestamp:
                                    type: string
                            kube-proxy:
                              type: array
                              items:
                                type: object
                                properties:
                                  name:
                                    type: string
                                  namespace:
                                    type: string
                                  status:
                                    type: string
                                  node_name:
                                    type: string
                                  creation_timestamp:
                                    type: string
                            coredns:
                              type: array
                              items:
                                type: object
                                properties:
                                  name:
                                    type: string
                                  namespace:
                                    type: string
                                  status:
                                    type: string
                                  node_name:
                                    type: string
                                  creation_timestamp:
                                    type: string
                        Networking:
                          type: object
                          properties:
                            slingshot-fabric-manager:
                              type: array
                              items:
                                type: object
                                properties:
                                  name:
                                    type: string
                                  namespace:
                                    type: string
                                  status:
                                    type: string
                                  node_name:
                                    type: string
                                  creation_timestamp:
                                    type: string
                        Work Load Manager:
                          type: object
                          properties:
                            pbs:
                              type: array
                              items:
                                type: object
                                properties:
                                  name:
                                    type: string
                                  namespace:
                                    type: string
                                  status:
                                    type: string
                                  node_name:
                                    type: string
                                  creation_timestamp:
                                    type: string
                            slurm:
                              type: array
                              items:
                                type: object
                                properties:
                                  name:
                                    type: string
                                  namespace:
                                    type: string
                                  status:
                                    type: string
                                  node_name:
                                    type: string
                                  creation_timestamp:
                                    type: string
                        iscsi:
                          type: array
                          items:
                            type: object
                            properties:
                              name:
                                type: string
                              namespace:
                                type: string
                              status:
                                type: string
                              node_name:
                                type: string
                              creation_timestamp:
                                type: string
                        ceph:
                          type: array
                          items:
                            type: object
                            properties:
                              name:
                                type: string
                              namespace:
                                type: string
                              status:
                                type: string
                              node_name:
                                type: string
                              creation_timestamp:
                                type: string
                        etcd:
                          type: array
                          items:
                            type: object
                            properties:
                              name:
                                type: string
                              namespace:
                                type: string
                              status:
                                type: string
                              node_name:
                                type: string
                              creation_timestamp:
                                type: string
                        postgres:
                          type: array
                          items:
                            type: object
                            properties:
                              name:
                                type: string
                              namespace:
                                type: string
                              status:
                                type: string
                              node_name:
                                type: string
                              creation_timestamp:
                                type: string
                        nexus:
                          type: array
                          items:
                            type: object
                            properties:
                              name:
                                type: string
                              namespace:
                                type: string
                              status:
                                type: string
                              node_name:
                                type: string
                              creation_timestamp:
                                type: string
                        cray-hbtd:
                          type: array
                          items:
                            type: object
                            properties:
                              name:
                                type: string
                              namespace:
                                type: string
                              status:
                                type: string
                              node_name:
                                type: string
                              creation_timestamp:
                                type: string
          404:
            description: Not Found
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    error:
                      type: string
        """
        if self.path == "/zones":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps(get_zone_data(), indent=2)
            self.wfile.write(response.encode("utf-8"))
        elif self.path == "/critical-pods":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps(get_critical_pods(), indent=2)
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