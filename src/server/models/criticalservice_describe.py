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
from resources.critical_services import *
from kubernetes import client
from resources.error_print import pretty_print_error

cm_name = "rrs-mon-static"
cm_namespace = "rack-resiliency"
cm_key = "critical-service-config.json"

def get_service_details(services, service_name):
    """Retrieve details of a specific critical service."""
    try:
        if service_name not in services:
            return {"error": "Service not found"}
        
        # Getting information of service
        service_info = services[service_name]
        namespace = service_info["namespace"]
        resource_type = service_info["type"]

        # Get all pods in the namespace and filter by owner reference
        filtered_pods, running_pods = get_namespaced_pods(service_info, service_name)

        # Get configured instances
        apps_v1 = client.AppsV1Api()
        configured_instances = None
        if resource_type == "Deployment":
            deployment = apps_v1.read_namespaced_deployment(service_name, namespace)
            configured_instances = deployment.spec.replicas
        elif resource_type == "StatefulSet":
            statefulset = apps_v1.read_namespaced_stateful_set(service_name, namespace)
            configured_instances = statefulset.spec.replicas
        elif resource_type == "DaemonSet":
            daemonset = apps_v1.read_namespaced_daemon_set(service_name, namespace)
            configured_instances = daemonset.status.desired_number_scheduled

        return {
            "Critical Service": {
                "Name": service_name,
                "Namespace": namespace,
                "Type": resource_type,
                "Configured Instances": configured_instances,
                "Currently Running Instances": running_pods, 
                "Pods": filtered_pods
            }
        }
    except Exception as e:
        return {"error": str(pretty_print_error(e))}

def describe_service(service_name):
    """Returning the response in JSON Format"""
    try:
        services = get_configmap(cm_name, cm_namespace, cm_key).get("critical-services", {})
        return jsonify(get_service_details(services, service_name))
    except Exception as e:
        return {"error": str(pretty_print_error(e))}