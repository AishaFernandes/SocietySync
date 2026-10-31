import json
import logging
import time

import boto3
import psycopg2

import config

logging.basicConfig(filename="/var/log/societysync/worker.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")

sqs = boto3.client("sqs", region_name="eu-north-1")
url = sqs.get_queue_url(QueueName="societysync-queue")["QueueUrl"]
log.info("worker started, queue %s", url)

while True:
    try:
        resp = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=10, WaitTimeSeconds=20)
        for m in resp.get("Messages", []):
            body = json.loads(m["Body"])
            if "TopicArn" in body and "Message" in body:  # SNS envelope
                body = json.loads(body["Message"])

            conn = psycopg2.connect(**config.DB)
            try:
                with conn, conn.cursor() as cur:
                    cur.execute("INSERT INTO notification_log (event_type, payload) VALUES (%s, %s)",
                                (body.get("event", "unknown"), json.dumps(body)))
            finally:
                conn.close()

            sqs.delete_message(QueueUrl=url, ReceiptHandle=m["ReceiptHandle"])
            log.info("processed %s", body.get("event"))
    except Exception as e:
        log.error("worker error: %s", e)
        time.sleep(5)