#!/bin/bash
set -e

echo "=========================================="
echo "Starting Niche Inbox Deployment on AWS EC2"
echo "=========================================="

echo "[1/6] Updating packages and installing dependencies..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install python3-pip python3-venv git -y

echo "[2/6] Cloning repository..."
cd /home/ubuntu
if [ -d "Niche-Inbox" ]; then
    echo "Directory exists, removing old clone..."
    rm -rf Niche-Inbox
fi
git clone https://github.com/Mrun25/Niche-Inbox.git
cd Niche-Inbox

echo "[3/6] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "[4/6] Moving secrets into place..."
mv ~/.env /home/ubuntu/Niche-Inbox/
mv ~/credentials.json /home/ubuntu/Niche-Inbox/
mv ~/token.json /home/ubuntu/Niche-Inbox/
if [ -f ~/digest.db ]; then
    mv ~/digest.db /home/ubuntu/Niche-Inbox/
fi

# Update the BASE_URL in the .env file to the EC2 Public IP
sed -i 's|^BASE_URL=.*|BASE_URL=http://13.201.55.92:5000|g' .env

echo "[5/6] Creating systemd service..."
cat << 'EOF' | sudo tee /etc/systemd/system/niche-inbox.service
[Unit]
Description=Niche Inbox App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Niche-Inbox
Environment="PATH=/home/ubuntu/Niche-Inbox/venv/bin"
ExecStart=/home/ubuntu/Niche-Inbox/venv/bin/python main.py
Restart=always
# Wait 10 seconds before restarting if it crashes
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "[6/6] Starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable niche-inbox
sudo systemctl restart niche-inbox

echo "=========================================="
echo "Deployment Complete!"
echo "App should be running at http://13.201.55.92:5000"
echo "=========================================="
