#!/bin/bash

# PiBQ Service Installation Script

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (use sudo)"
    exit 1
fi

echo "Installing PiBQ systemd services..."

# Copy service files to systemd directory
cp pibq-recorder.service /etc/systemd/system/
cp pibq-dashboard.service /etc/systemd/system/

# Set proper permissions
chmod 644 /etc/systemd/system/pibq-recorder.service
chmod 644 /etc/systemd/system/pibq-dashboard.service

# Reload systemd daemon
systemctl daemon-reload

# Enable services (they will start automatically on boot)
systemctl enable pibq-recorder.service
systemctl enable pibq-dashboard.service

echo "Services installed and enabled!"
echo ""
echo "To start the services now:"
echo "  sudo systemctl start pibq-recorder"
echo "  sudo systemctl start pibq-dashboard"
echo ""
echo "To check service status:"
echo "  sudo systemctl status pibq-recorder"
echo "  sudo systemctl status pibq-dashboard"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u pibq-recorder -f"
echo "  sudo journalctl -u pibq-dashboard -f"
echo ""
echo "To stop services:"
echo "  sudo systemctl stop pibq-dashboard"
echo "  sudo systemctl stop pibq-recorder"