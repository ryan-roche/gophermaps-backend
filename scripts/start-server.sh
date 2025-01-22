#!/bin/bash

# Get secrets from parameter store and set them as environment variables for the service
aws ssm get-parameters-by-path \
    --path "/GopherMaps/" \
    --recursive \
    --with-decryption \
    --region us-east-2 \
    --query 'Parameters[*].[Name,Value]' \
    --output text | \
while IFS=$'\t' read -r name value; do
    param_name=$(basename "$name" | tr '-' '_')
    sudo systemctl set-environment "$param_name=$value"
done

# Start the service
systemctl start gophermaps.service