# SocietySync
A cloud-hosted housing-society web app on AWS (region eu-north-1, Stockholm). Residents register, read notices and raise complaints with optional file attachments. Admins post notices and update complaint status.

## Architecture
![SocietySync Architecture Diagram](main/SocietySync AWS Architecture Diagram.png)



## Repository layout
Path | Purpose
---|---
app.py | Flask application: routes, auth, S3 upload/download, SNS publishing
ui.py | HTML/CSS templates (layout, login, notices, complaints)
config.py | Reads settings and secrets from Parameter Store at start-up
worker.py | Background SQS consumer that records events in notification log
db/schema.sql | PostgreSQL schema (users, notices, complaints, notification_log)
deploy/ | systemd units, nginx config, CloudWatch agent config, psql helper
requirements.txt | Python dependencies

## AWS resources the code expects
- VPC societysync-vpc with public and private subnets; security groups societysync-ec2-sg and societysync-rds-sg
- RDS PostgreSQL societysync-db (private), database societysync
- S3 bucket societysync-private-20261028-01 (Block Public Access on)
- SNS topic societysync-events (Standard), SQS queues societysync-queue and societysync-dlq (Standard, max receives 3)
- Parameter Store: /societysync/db-host, db-name, db-user (String); db-password, secret-key (SecureString)
- IAM role SocietySync-EC2-Role with S3, SSM parameter read, SNS publish, SQS access, AmazonSSMManagedInstanceCore and CloudWatchAgentServerPolicy

## Run on EC2 (Amazon Linux 2023)
```bash
sudo dnf install -y python3-pip git nginx postgresql15
sudo mkdir -p /var/log/societysync && sudo chown ec2-user: /var/log/societysync
cd /societysync
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
source deploy/dbenv.sh
psql -v ON_ERROR_STOP=1 -f db/schema.sql
sudo cp deploy/societysync.service deploy/societysync-worker.service /etc/systemd/system/
sudo cp deploy/nginx.conf /etc/nginx/nginx.conf
sudo systemctl daemon-reload
sudo systemctl enable --now societysync societysync-worker nginx
curl localhost/health
