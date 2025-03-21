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

import json
# import rados
import subprocess
import concurrent.futures
# def get_ceph_details():
#     """Fetch Ceph OSD tree details using rados."""
#     try:
#         cluster = rados.Rados(conffile="/etc/ceph/ceph.conf")
#         cluster.conf_set('keyring', '/etc/ceph/ceph.client.admin.keyring')
#         cluster.connect()

#         cmd = json.dumps({"prefix": "osd tree", "format": "json-pretty"})
#         result = cluster.mon_command(cmd, b'')
#         cluster.shutdown()

#         if isinstance(result, tuple) and len(result) >= 2:
#             json_data = result[1].decode()
#         else:
#             raise ValueError(f"Unexpected return format: {result}")

#         return json.loads(json_data)
#     except Exception as e:
#         return {"error": str(e)}

# def get_ceph_hosts():
#     """Fetch Ceph storage node statuses using rados."""
#     try:
#         cluster = rados.Rados(conffile="/etc/ceph/ceph.conf")
#         cluster.conf_set('keyring', '/etc/ceph/ceph.client.admin.keyring')
#         cluster.connect()

#         cmd = json.dumps({"prefix": "orch host ls", "format": "json-pretty"})
#         result = cluster.mon_command(cmd, b'')
#         cluster.shutdown()

#         if isinstance(result, tuple) and len(result) >= 2:
#             json_data = result[1].decode()
#         else:
#             raise ValueError(f"Unexpected return format: {result}")

#         return json.loads(json_data)
#     except Exception as e:
#         return {"error": str(e)}

host = 'ncn-m001'
# def get_ceph_details():
#     """Function to fetch the CEPH OSD details using ssh"""
#     cmd = f"ssh {host} 'ceph osd tree -f json-pretty'"
#     try:
#         result = subprocess.run(cmd,shell=True,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,)
#         if result.returncode != 0:
#             raise ValueError(f"Error fetching Ceph details: {result.stderr}")
#         return json.loads(result.stdout)
#     except Exception as e:
#         return {"error": str(e)}

# def get_ceph_hosts():
#     """Function to fetch the hosts details using ssh"""
#     cmd = f"ssh {host} 'ceph orch host ls -f json-pretty'"
#     try:
#         result = subprocess.run(cmd,shell=True,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,)
#         if result.returncode != 0:
#             raise ValueError(f"Error fetching Ceph details: {result.stderr}")
#         return json.loads(result.stdout)
#     except Exception as e:
#         return {"error": str(e)}

def fetch_ceph_data():
    """Fetch Ceph OSD and host details in parallel."""
    ceph_details_cmd = "ssh ncn-m001 'ceph osd tree -f json-pretty'"
    ceph_hosts_cmd = "ssh ncn-m001 'ceph orch host ls -f json-pretty'"
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_ceph_tree = executor.submit(subprocess.run, ceph_details_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        future_ceph_hosts = executor.submit(subprocess.run, ceph_hosts_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        ceph_tree_result = future_ceph_tree.result()
        ceph_hosts_result = future_ceph_hosts.result()

        if ceph_tree_result.returncode != 0 or ceph_hosts_result.returncode != 0:
            raise ValueError(f"Error fetching Ceph details: {ceph_tree_result.stderr} / {ceph_hosts_result.stderr}")
        
        ceph_tree = json.loads(ceph_tree_result.stdout)
        ceph_hosts = json.loads(ceph_hosts_result.stdout)
        
        return ceph_tree, ceph_hosts

def get_ceph_storage_nodes():
    """Fetch Ceph storage nodes and their OSD statuses."""
    # ceph_tree = get_ceph_details()
    # ceph_hosts = get_ceph_hosts()
    ceph_tree, ceph_hosts = fetch_ceph_data()

    if isinstance(ceph_tree, dict) and "error" in ceph_tree:
        return {"error": ceph_tree["error"]}
    
    if isinstance(ceph_hosts, dict) and "error" in ceph_hosts:
        return {"error": ceph_hosts["error"]}

    host_status_map = {host["hostname"]: host["status"] for host in ceph_hosts}

    zones = {}

    for item in ceph_tree.get('nodes', []):
        if item['type'] == 'rack':  # Zone (Rack)
            rack_name = item['name']
            storage_nodes = []

            for child_id in item.get('children', []):
                host_node = next((x for x in ceph_tree['nodes'] if x['id'] == child_id), None)

                if host_node and host_node['type'] == 'host' and host_node['name'].startswith("ncn-s"):
                    osd_ids = host_node.get('children', [])
                    
                    osds = [osd for osd in ceph_tree['nodes'] if osd['id'] in osd_ids and osd['type'] == 'osd']
                    osd_status_list = [{"name": osd['name'], "status": osd.get('status', 'unknown')} for osd in osds]

                    node_status = host_status_map.get(host_node['name'], "No Status")
                    if node_status in ["", "online"]:
                        node_status = "Ready"

                    storage_nodes.append({
                        "name": host_node['name'],
                        "status": node_status,
                        "osds": osd_status_list
                    })

            zones[rack_name] = storage_nodes

    return zones if zones else "No Ceph zones present"
