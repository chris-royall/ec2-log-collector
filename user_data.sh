#!/bin/bash

apt update -y
apt install -y unzip

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

mkdir -p /usr/local/bin
mkdir -p /etc/systemd/system

cat << 'EOF' > /usr/local/bin/log_collector.sh
#!/bin/bash

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUCKET_NAME="REPLACE"
LOG_FILE="/var/log/log-collector.log"
TEMP_DIR="/tmp/logs"
STATE_FILE="/tmp/last_log_collection"

echo "Log collection started at $TIMESTAMP" >> "$LOG_FILE"

# Create temp directory
mkdir -p "$TEMP_DIR"

# Get timestamp from 1 hour ago
SINCE=$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')

# Collect only new logs from the last hour
journalctl --since "$SINCE" --no-pager > "$TEMP_DIR/new_logs_${TIMESTAMP}.log"

# Only upload if there are new logs
if [[ -s "$TEMP_DIR/new_logs_${TIMESTAMP}.log" ]]; then
    gzip "$TEMP_DIR/new_logs_${TIMESTAMP}.log"
    aws s3 cp "$TEMP_DIR/new_logs_${TIMESTAMP}.log.gz" "s3://$BUCKET_NAME/logs/"
fi

# Success / Failure logging
if [[ $? -eq 0 ]]; then
    echo "Log upload successful at $TIMESTAMP" >> "$LOG_FILE"
else
    echo "Log upload failed at $TIMESTAMP" >> "$LOG_FILE"
fi

# Clean up
rm -rf "$TEMP_DIR"

EOF

chmod +x /usr/local/bin/log_collector.sh

cat << 'EOF' > /etc/systemd/system/log-collector.service
[Unit]
Description=Collect and upload logs to S3

[Service]
Type=oneshot
ExecStart=/usr/local/bin/log_collector.sh

EOF

cat << 'EOF' > /etc/systemd/system/log-collector.timer
[Unit]
Description=Run log collector every hour

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target

EOF

systemctl daemon-reload
systemctl enable --now log-collector.timer
