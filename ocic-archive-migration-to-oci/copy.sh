#!/bin/bash

# Edit these settings for the OCI-C source container
export SOURCE_CONTAINER=<container>
export SOURCE_CONTAINER_SERVICE_INSTANCE=<instance>
export SOURCE_CONTAINER_USER=<user>
export RCLONE_CONFIG_OCIC_KEY=<key>
export RCLONE_CONFIG_OCIC_AUTH=<auth url>

# Edit these settings for the OCI destination bucket
export DESTINATION_BUCKET=<bucket>
export DESTINATION_BUCKET_NAMESPACE=<namespace>
export RCLONE_CONFIG_OCI_ACCESS_KEY_ID=<access key>
export RCLONE_CONFIG_OCI_SECRET_ACCESS_KEY=<secret key>
export RCLONE_CONFIG_OCI_REGION=<region>

# 
# Should not need to edit below this line
#

export RCLONE_CONFIG_OCIC_TYPE=swift
export RCLONE_CONFIG_OCIC_USER=$SOURCE_CONTAINER_SERVICE_INSTANCE:$SOURCE_CONTAINER_USER

export RCLONE_CONFIG_OCI_TYPE=s3
export RCLONE_CONFIG_OCI_ENDPOINT=https://$DESTINATION_BUCKET_NAMESPACE.compat.objectstorage.$RCLONE_CONFIG_OCI_REGION.oraclecloud.com

for F in $(./archive-restore.py --quiet --list-objects $SOURCE_CONTAINER); do
	echo Copying OCI-C:$SOURCE_CONTAINER/$F -\> OCI:$DESTINATION_BUCKET/$F
	rclone copy OCIC:$SOURCE_CONTAINER/$F OCI:$DESTINATION_BUCKET/
done
