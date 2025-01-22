#!/bin/bash

# Get secrets from parameter store and set them as environment variables for the service
aws ssm get-parameters-by-path \
    --path "/your/param/path" \
    --with-decryption \
    --region your-region \
    --query 'Parameters[*].[Name,Value]' \
    --output text | \
while read -r name value; do
    param_name=$(basename "$name")
    systemctl set-environment "$param_name=$value"
done

# Start the service
systemctl start gophermaps.service