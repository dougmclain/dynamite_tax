#!/bin/bash
# Create media directories in the mounted disk
mkdir -p /var/lib/render/disk/media/completed_tax_returns
mkdir -p /var/lib/render/disk/media/extensions
mkdir -p /var/lib/render/disk/media/engagement_letters
mkdir -p /var/lib/render/disk/media/signed_engagement_letters

# Set permissions
chmod -R 777 /var/lib/render/disk/media

# Start the application
exec gunicorn HOA_tax.wsgi:application "$@"