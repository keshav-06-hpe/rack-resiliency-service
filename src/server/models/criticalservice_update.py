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
from flask import jsonify
from kubernetes import client
from resources.critical_services import *
from resources.error_print import pretty_print_error

cm_name = "rrs-mon-static"
cm_namespace = "rack-resiliency"
cm_key = "critical-service-config.json"

# def serviceExist(service_name,new_services):
#     """Function to check if the service to be updated has any instances running on cluster"""
#     try:
#         service_info = new_services[service_name]

#         # Get all pods in the namespace and filter by owner reference
#         filtered_pods = get_namespaced_pods(service_info, service_name)

#         # Get all services in the namespace and filter by label selector
#         filtered_services = get_namespaced_services(service_info, service_name)

#         if len(filtered_pods[0]) == 0 and len(filtered_services) == 0:
#             return False
#         return True
    
#     except Exception as e:
#         return {"error": str(e)} 

def update_configmap(new_data, existing_data, test=False):
    """Update the ConfigMap in the Kubernetes cluster with the merged data."""
    try:
        v1 = client.CoreV1Api()
        # Fetch the existing ConfigMap data
        # existing_data = get_configmap()
        if "error" in existing_data:
            return existing_data
        
        # Merge the existing and new data
        existing_services = existing_data.get("critical-services", {})
        new_services = json.loads(new_data)

        # Merge new services, checking for duplicates
        added_services = []
        skipped_services = []
        # non_existing_services = []
        for service_name, details in new_services["critical-services"].items():
            if service_name in existing_services:
                skipped_services.append(service_name)
            else:
                # if serviceExist(service_name, new_services["critical-services"]):
                    existing_services[service_name] = details
                    added_services.append(service_name)
                # else:
                    # non_existing_services.append(service_name)

        # Convert back to JSON string for ConfigMap storage
        updated_json_str = json.dumps({"critical-services": existing_services}, indent=2)

        # Patch the ConfigMap with the updated data
        body = {"data": {cm_key: updated_json_str}}
        
        # Added the condition for CI testcase
        if not(test):
            v1.patch_namespaced_config_map(cm_name, cm_namespace, body)

        response = {"Update": "Successful"}

        if added_services:
            response["Successfully Added Services"] = added_services
        if skipped_services:
            response["Already Existing Services"] = skipped_services
            if len(added_services) == 0:
                response["Update"] = "Services Already Exist"
        # if non_existing_services:
        #     response["Unknown Services"] = non_existing_services
        #     response["Message for unknown services"] = (
        #         "Service(s) has no associated pods in the namespace, Please verify the Information"
        #     )
        # else:
        #     response["Update"] = "Unsuccessful"
        return response

    except Exception as e:
        return {"error": str(pretty_print_error(e))}

    except client.exceptions.ApiException as e:
        return {"error": f"Failed to update ConfigMap: {pretty_print_error(e)}"}

def update_critical_services(new_data):
    """Function to update critical services in the ConfigMap."""
    try:
        if not new_data or "from_file" not in new_data:
            return jsonify({"error": "Invalid request format"}), 400

        # Parse the nested JSON string inside "services"
        try:
            new_data = new_data.get("from_file")
            new_services = json.loads(new_data)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format in services"}), 400

        if "critical-services" not in new_services:
            return jsonify({"error": "Missing 'critical-services' in payload"}), 400
        
        existing_data = get_configmap(cm_name, cm_namespace, cm_key)
        result = update_configmap(new_data, existing_data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(pretty_print_error(e))}), 500
