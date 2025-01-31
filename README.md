# Rack Resiliency Service

This project provides a Kubernetes-based service designed to monitor and ensure the resiliency of rack-based systems. It includes automatic recovery mechanisms and detailed logging for seamless rack operation.

## Features
- Rack health monitoring
- Automatic recovery for racks
- Integrates with Kubernetes

## Installation

Clone the repository:
```bash
git clone https://github.com/keshav-06-hpe/rack-resiliency-service.git
```
<br>
Build the Docker image:
   ```bash
   docker build -t <your-dockerhub-username>/zone-lister:latest ./app
   docker push <your-dockerhub-username>/zone-lister:latest
```