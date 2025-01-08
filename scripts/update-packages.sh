#!/bin/bash

# Use poetry to "refresh" packages to match pyproject.toml
cd /var/gophermaps || { echo "Failed to find install directory!"; exit 1; }
poetry lock
poetry install