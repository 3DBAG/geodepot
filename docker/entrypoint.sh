#!/bin/bash
set -e
# Inject SSH public key if provided via environment variable
if [ -n "$SSH_PUBLIC_KEY" ]; then
    echo "$SSH_PUBLIC_KEY" >> /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
fi
# Start nginx in background, sshd in foreground
nginx
exec /usr/sbin/sshd -D
