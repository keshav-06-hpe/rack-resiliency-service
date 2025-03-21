#
# MIT License
#
# (C) Copyright [2024-2025] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#

from resources.k8sZones import get_k8s_nodes_data
from resources.cephZones import get_ceph_storage_nodes
from flask import jsonify

def zoneExist(k8s_zones, ceph_zones):
    """Function to check if any types of zones(K8s Topology or CEPH) exist"""
    if isinstance(k8s_zones, str) and isinstance(ceph_zones, str):
        return {"Zones": [], "Information": "No zones (K8s topology and Ceph) configured"}
    if isinstance(k8s_zones, str):
        return {"Zones": [], "Information": "No K8s topology zones configured"}
    if isinstance(ceph_zones, str):
        return {"Zones": [], "Information": "No CEPH zones configured"}

def get_node_name(node_list):
    """Extracts node names from a list of node dictionaries."""
    return [node.get("name") for node in node_list if "name" in node]

def map_zones(k8s_zones, ceph_zones):
    """Map Kubernetes and Ceph zones and provide summarized data in the new format."""
    if isinstance(k8s_zones, dict) and "error" in k8s_zones:
        return {"error": k8s_zones["error"]}
    
    if isinstance(ceph_zones, dict) and "error" in ceph_zones:
        return {"error": ceph_zones["error"]}
    
    if isinstance(k8s_zones, str) or isinstance(ceph_zones, str):
        return zoneExist(k8s_zones, ceph_zones)
    
    all_zone_names = set(k8s_zones.keys()) | set(ceph_zones.keys())
    zones_list = []

    for zone_name in all_zone_names:
        masters = get_node_name(k8s_zones.get(zone_name, {}).get("masters", []))
        workers = get_node_name(k8s_zones.get(zone_name, {}).get("workers", []))
        storage = get_node_name(ceph_zones.get(zone_name, []))

        zone_data = {"Zone Name": zone_name}
        
        if masters or workers:
            zone_data["Kubernetes Topology Zone"] = {}
            if masters:
                zone_data["Kubernetes Topology Zone"]["Management Master Nodes"] = masters
            if workers:
                zone_data["Kubernetes Topology Zone"]["Management Worker Nodes"] = workers
        
        if storage:
            zone_data["CEPH Zone"] = {"Management Storage Nodes": storage}
        
        zones_list.append(zone_data)

    return {"Zones": zones_list}

def get_zones():
    """Endpoint to get summary of all zones in the new format."""
    k8s_zones = get_k8s_nodes_data()
    ceph_zones = get_ceph_storage_nodes()
    return jsonify(map_zones(k8s_zones, ceph_zones))