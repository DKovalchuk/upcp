#!/bin/bash
# Add local domains for UPCP environments
# Run with sudo: sudo ./setup-hosts.sh

DOMAINS=(
    "127.0.0.1 upcp.local"
    "127.0.0.1 dev.upcp.local"
    "127.0.0.1 test.upcp.local"
)

HOSTS_FILE="/etc/hosts"

for entry in "${DOMAINS[@]}"; do
    if ! grep -q "$entry" "$HOSTS_FILE" 2>/dev/null; then
        echo "$entry" >> "$HOSTS_FILE"
        echo "Added: $entry"
    else
        echo "Already exists: $entry"
    fi
done

echo ""
echo "Domains configured:"
echo "  upcp.local       → stage  (port 3080)"
echo "  dev.upcp.local   → dev    (port 3081)"
echo "  test.upcp.local  → test   (port 3082)"
