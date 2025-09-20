#!/bin/bash
# LSL Firewall Setup Script for Server
# Run with: sudo bash config/setup_lsl_firewall.sh

echo "Setting up firewall rules for LSL cross-network communication..."
echo "Port range: 3051-3067 (UDP 3051 for discovery, TCP/UDP 3052-3067 for data)"

# Allow LSL discovery port (UDP 3051)
echo "Opening UDP 3051 for LSL discovery..."
ufw allow 3051/udp

# Allow LSL data ports (TCP/UDP 3052-3067)
echo "Opening TCP/UDP range 3052-3067 for LSL data streams..."
ufw allow 3052:3067/tcp
ufw allow 3052:3067/udp

# Check firewall status
echo "Current firewall rules:"
ufw status numbered

echo "LSL firewall setup completed!"
echo ""
echo "Next steps:"
echo "1. Place config/lsl_api_server.cfg at ~/lsl_api/lsl_api.cfg (replace <YOUR_HOME_PUBLIC_IP>)"
echo "2. Configure your home router to forward UDP 3051 and TCP/UDP 3052-3067 to your local computer"
echo "3. Place config/lsl_api_local.cfg at ~/lsl_api/lsl_api.cfg on your local computer (replace <SERVER_PUBLIC_IP>)"