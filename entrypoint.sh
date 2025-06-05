#!/bin/sh
# Fix SSH key permissions for mounted keys
chmod 600 /root/.ssh/id_ed25519
chmod 644 /root/.ssh/id_ed25519.pub
chmod 644 /root/.ssh/known_hosts

# Run the main command passed to the container
exec "$@"
