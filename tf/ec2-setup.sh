#!/bin/bash

# Install git, python, and pip
dnf update -y
dnf install -y git
dnf install -y python3.11
dnf install -y python3.11-pip

# Install poetry using pip
pip3.11 install poetry==1.8.3

# Create directory structure
mkdir -p /var/gophermaps/app

# Define the service for the FastAPI app that'll be used in the CodeDeploy scripts
cat << 'EOF' > /etc/systemd/system/gophermaps.service
[Unit]
Description=GopherMaps FastAPI Application
After=network.target

[Service]
WorkingDirectory=/var/gophermaps/app
ExecStart=/usr/local/bin/poetry run uvicorn main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl enable gophermaps.service
