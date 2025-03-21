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

from flask import jsonify
from resources.k8sZones import get_k8s_nodes_data
from resources.cephZones import get_ceph_storage_nodes
from models.zoneList import zoneExist

def get_zone_info(zone_name,k8s_zones,ceph_zones):
    """Function to get detailed information of a specific zone."""
    if isinstance(k8s_zones, dict) and "error" in k8s_zones:
        return {"error": k8s_zones["error"]}
    
    if isinstance(ceph_zones, dict) and "error" in ceph_zones:
        return {"error": ceph_zones["error"]}
    
    if isinstance(k8s_zones, str) or isinstance(ceph_zones, str):
        return zoneExist(k8s_zones, ceph_zones)

    masters = k8s_zones.get(zone_name, {}).get("masters", [])
    workers = k8s_zones.get(zone_name, {}).get("workers", [])
    storage = ceph_zones.get(zone_name, [])

    if not (masters or workers or storage):
        return {"error": "Zone not found"}

    zone_data = {
        "Zone Name": zone_name,
        "Management Masters": len(masters),
        "Management Workers": len(workers),
        "Management Storages": len(storage)
    }

    if masters:
        zone_data["Management Master"] = {
            "Type": "Kubernetes Topology Zone",
            "Nodes": [{"Name": node["name"], "Status": node["status"]} for node in masters]
        }
    
    if workers:
        zone_data["Management Worker"] = {
            "Type": "Kubernetes Topology Zone",
            "Nodes": [{"Name": node["name"], "Status": node["status"]} for node in workers]
        }
    
    if storage:
        zone_data["Management Storage"] = {
            "Type": "CEPH Zone",
            "Nodes": []
        }
        for node in storage:
            osd_status_map = {}
            for osd in node.get("osds", []):
                osd_status_map.setdefault(osd["status"], []).append(osd["name"])
            
            storage_node = {
                "Name": node["name"],
                "Status": node["status"],
                "OSDs": osd_status_map
            }
            zone_data["Management Storage"]["Nodes"].append(storage_node)
    
    return zone_data

def describe_zone(zone_name):
    k8s_zones = get_k8s_nodes_data()
    ceph_zones = get_ceph_storage_nodes()
    return jsonify(get_zone_info(zone_name, k8s_zones, ceph_zones))