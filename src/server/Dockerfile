FROM --platform=linux/amd64 python:3.9-slim as build
# Use the SLES base image
FROM registry.suse.com/suse/sle15:latest

# Set environment variables
ENV KUBECTL_VERSION=v1.28.0  

# Update package manager and install necessary dependencies
RUN zypper refresh && \
    zypper install -y curl ca-certificates python3 python3-pip && \
    zypper clean && \
    update-ca-certificates

# Install kubectl securely
RUN curl --insecure -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/kubectl


# Set the working directory in the container
WORKDIR /src/server

# Copy the current directory contents into the container
COPY app.py .

EXPOSE 8080

# Run the server
CMD ["python", "app.py"]
