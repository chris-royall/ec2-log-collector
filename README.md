# EC2 Log Collector

Automated Linux system log collection from EC2 instances to S3 using systemd timers.

## Overview

This project provides an automated solution for collecting and uploading Linux system logs from EC2 instances to Amazon S3. The system uses systemd timers to run log collection tasks on a scheduled basis, ensuring reliable and consistent log management.

## Architecture

```
EC2 Instance
├── systemd timer (hourly trigger)
├── log-collector.service
├── log_collector.sh (collection script)
└── S3 upload (compressed logs)
```

## Project Structure

```
ec2-log-collector/
├── deploy_ec2.py          # Main deployment script
├── log_collector.sh       # Log collection and upload script
├── user_data.sh          # EC2 instance initialization script
├── systemd/              # Systemd service and timer configuration files
└── README.md             # This file
```

## File Descriptions

| File | Purpose |
|------|----------|
| `deploy_ec2.py` | Main deployment script that provisions EC2 instance and S3 bucket |
| `log_collector.sh` | Core script that collects system logs and uploads to S3 |
| `user_data.sh` | EC2 user data script for instance initialization and setup |
| `systemd/` | Directory containing systemd service and timer configuration files |

## System Operation Examples


### Timer Status and Configuration

**Checking timer status:**
```
ubuntu@ip-xxxxx~$ systemctl status log-collector.timer
● log-collector.timer - Run log collector every hour
     Loaded: loaded (/etc/systemd/system/log-collector.timer; enabled; preset: enabled)
     Active: active (waiting) since Sun 2026-01-18 18:24:45 UTC; 2min 2s ago
    Trigger: Sun 2026-01-18 19:00:00 UTC; 33min left
   Triggers: ● log-collector.service

Jan 18 18:24:45 ip-xxxxx systemd[1]: Started log-collector.timer - Run log collector every hour.
```

### Log Collection Service

**Service execution status:**
```
ubuntu@ip-xxxxx:~$ systemctl status log-collector.service
○ log-collector.service - Collect and upload logs to S3
     Loaded: loaded (/etc/systemd/system/log-collector.service; static)
     Active: inactive (dead) since Sun 2026-01-18 19:00:30 UTC; 31min ago
TriggeredBy: ● log-collector.timer
    Process: 1250 ExecStart=/usr/local/bin/log_collector.sh (code=exited, status=0/SUCCESS)
   Main PID: 1250 (code=exited, status=0/SUCCESS)
        CPU: 1.321s

Jan 18 19:00:28 ip-xxxxx systemd[1]: Starting log-collector.service - Collect and upload logs to S3...
Jan 18 19:00:30 ip-xxxxx log_collector.sh[1259]: [215B blob data]
Jan 18 19:00:30 ip-xxxxx systemd[1]: log-collector.service: Deactivated successfully.
Jan 18 19:00:31 ip-xxxxx systemd[1]: Finished log-collector.service - Collect and upload logs to S3.
Jan 18 19:00:31 ip-xxxxx systemd[1]: log-collector.service: Consumed 1.321s CPU time.
```

### Local Log Monitoring

**Application log verification:**
```
ubuntu@ip-xxxxx:~$ tail -2 /var/log/log-collector.log
Log collection started at 20260118_190028
Log upload successful at 20260118_190028
```

### S3 Upload Verification

**Confirming successful uploads to S3:**
```
<username>@<hostname> ec2-log-collector % aws s3 ls s3://ec2-log-collector-xxxxx/logs/    
2026-01-18 19:00:31      58393 new_logs_20260118_190028.log.gz
```

## Log Collection Details

- **Frequency**: Hourly collection via systemd timer
- **Compression**: Logs are gzipped before upload
- **Naming Convention**: `new_logs_YYYYMMDD_HHMMSS.log.gz`
- **Storage**: Uploaded to S3 bucket with organized folder structure
