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

from flask import Flask, request
from models.zone_list import get_zones
from models.zone_describe import describe_zone
from models.criticalservice_list import get_critical_service_list
from models.criticalservice_describe import describe_service
from models.criticalservice_update import update_critical_services
from models.criticalservice_status_list import get_critical_services_status
app = Flask(__name__)

# Endpoint to get the list of zones
@app.route("/zones", methods=["GET"])
def listZones():
    return get_zones()

# Endpoint to describe the zone entered
@app.route('/zones/<zone_name>', methods=['GET'])
def desc_zone(zone_name):
    return describe_zone(zone_name)

# Endpoint to get the list of critical services
@app.route('/criticalservices', methods=['GET'])
def listCriticalService():
    return get_critical_service_list()

# Endpoint to describe the critical service entered
@app.route("/criticalservices/<service_name>", methods=["GET"])
def describeCriticalService(service_name):
    return describe_service(service_name)

# Endpoint to update the critical services list
@app.route("/criticalservices", methods=["PATCH"])
def updateCriticalService():
    new_data = request.get_json()
    return update_critical_services(new_data)

# Endpoint to get the list of critical services status
@app.route("/criticalservices/status", methods=["GET"])
def listStatusCrtiticalServices():
    return get_critical_services_status()

# Running the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
