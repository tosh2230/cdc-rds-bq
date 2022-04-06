import base64
import io
import json
import logging
import os
import urllib
from typing import Tuple

import boto3
from google.cloud import bigquery
from google.oauth2 import service_account

# logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LambdaProcessor(object):
    def __init__(
        self,
        event: dict,
        context: dict,
    ):
        self.event = event
        self.context = context

    def main(self) -> dict:
        bucket_name, key = self.read_s3_event(event=self.event)
        previous_rows, current_rows = self.load_file_to_bq(
            dataset_id=key.split('/')[0],
            table_id=key.split('/')[1],
            file_obj=self.get_s3_object_body(bucket_name=bucket_name, key=key),
            service_account_info=self.get_service_account_info(secret_id=os.environ["GCP_SA_SECRET_NAME"]),
        )

        return {
            "PreviousRows": previous_rows,
            "CurrentRows": current_rows,
        }

    @staticmethod
    def read_s3_event(event: dict) -> Tuple[str, str]:
        s3_event = event["Records"][0]["s3"]
        bucket_name = s3_event["bucket"]["name"]
        key = urllib.parse.unquote_plus(
            s3_event["object"]["key"], encoding="utf-8"
        )
        return bucket_name, key

    def get_s3_object_body(self, bucket_name: str, key: str) -> io.BytesIO:
        client = boto3.resource('s3')
        buffer = io.BytesIO()
        object = client.Object(bucket_name, key)
        object.download_fileobj(buffer)
        buffer.seek(0)
        return buffer

    def get_service_account_info(self, secret_id: str) -> dict:
        service_account_info: str
        sm_client = boto3.client(service_name="secretsmanager", region_name=os.environ["AWS_REGION"])
        response = sm_client.get_secret_value(
            SecretId=secret_id
        )
        if 'SecretString' in response:
            service_account_info = response['SecretString']
        else:
            service_account_info = base64.b64decode(response['SecretBinary'])
        return json.loads(service_account_info)

    def load_file_to_bq(
        self,
        dataset_id: str,
        table_id: str,
        file_obj: io.BytesIO,
        service_account_info: dict
    ) -> Tuple[int, int]:
        credentials = service_account.Credentials.from_service_account_info(info=service_account_info)
        bq_client = bigquery.Client(credentials=credentials)

        destination = f"{dataset_id}.{table_id}"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True,
        )

        job = bq_client.load_table_from_file(
            file_obj=file_obj,
            destination=destination,
            job_config=job_config,
        )
        job.result()
        current_rows = bq_client.get_table(table=destination).num_rows
        return current_rows


def lambda_handler(event, context) -> dict:
    processor = LambdaProcessor(
        event=event,
        context=context,
    )
    return processor.main()
