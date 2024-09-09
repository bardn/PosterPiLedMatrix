#!/bin/bash

# Update package list and install required packages
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev fbi python3-pillow

# Install Python packages from requirements.txt
pip3 install -r requirements.txt

# Get the current user and group
USER=$(whoami)
GROUP=$(id -gn)

# Download the rgb-matrix.sh script from the Adafruit repository
curl -O https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh

# Make the script executable
chmod +x rgb-matrix.sh

# Run the script with sudo
sudo ./rgb-matrix.sh

# Create systemd service file
cat <<EOF | sudo tee /etc/systemd/system/poster.service
[Unit]
Description=Poster Display Script
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/PosterPiLedMatrix/posters.py
WorkingDirectory=/home/pi/PosterPiLedMatrix
StandardOutput=inherit
StandardError=inherit
Restart=always
User=$USER
Group=$GROUP

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable poster.service
sudo systemctl start poster.service

echo "Setup complete."
echo "Do you want to reboot the system now to apply changes? (y/n)"
read -r REBOOT

if [ "$REBOOT" = "y" ] || [ "$REBOOT" = "Y" ]; then
    echo "Rebooting the system..."
    sudo reboot
else
    echo "You can manually reboot the system later to apply changes."
fi
