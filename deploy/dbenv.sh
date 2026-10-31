#!/bin/bash
# Helper for psql on the EC2 server. Loads DB settings from Parameter Store.
# No password is stored in this file. Usage: source deploy/dbenv.sh

export AWS_DEFAULT_REGION=eu-north-1
export PGHOST=$(aws ssm get-parameter --name /societysync/db-host --query Parameter.Value --output text)
export PGDATABASE=$(aws ssm get-parameter --name /societysync/db-name --query Parameter.Value --output text)
export PGUSER=$(aws ssm get-parameter --name /societysync/db-user --query Parameter.Value --output text)
export PGPASSWORD=$(aws ssm get-parameter --name /societysync/db-password --with-decryption --query Parameter.Value --output text)
export PGSSLMODE=require