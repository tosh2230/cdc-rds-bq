import base64
import json
import logging
import os
import urllib
from typing import IO, Tuple

from boto3 import Session
from boto3.resources.base import ServiceResource
from botocore.config import Config
from google.cloud import bigquery
from google.oauth2 import service_account

# logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

endpoint = os.environ["ENDPOINT"]
s3_endpoint_url = os.environ["S3_ENDPOINT_URL"]
sm_endpoint_url = os.environ["SECRETS_MANAGER_ENDPOINT_URL"]
aws_region = os.environ["AWS_REGION"]
gcp_sa_secret_name = os.environ["GCP_SA_SECRET_NAME"]

session = Session()
s3_client: ServiceResource
sm_client: ServiceResource


class LambdaProcessor(object):
    def __init__(
        self,
        event: dict,
        context: dict,
        s3_client: ServiceResource,
        sm_client: ServiceResource,
        gcp_sa_secret_name: str,
    ):
        self.event = event
        self.context = context
        self.s3_client = s3_client
        self.sm_client = sm_client
        self.gcp_sa_secret_name = gcp_sa_secret_name

    def main(self) -> dict:
        bucket_name, key = self.read_s3_event(event=self.event)
        previous_rows, current_rows = self.load_file_to_bq(
            dataset_id=key.split('/')[0],
            table_id=key.split('/')[1],
            file_obj=self.get_s3_object_body(bucket_name=bucket_name, key=key),
            service_account_info=self.get_service_account_info(secret_id=self.gcp_sa_secret_name),
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

    def get_s3_object_body(self, bucket_name: str, key: str) -> IO[bytes]:
        return (
            self.s3_client.meta.client
            .get_object(Bucket=bucket_name, Key=key)["Body"]
            .read()
            .decode("utf-8")
        )

    def get_service_account_info(self, secret_id: str) -> dict:
        service_account_info: str
        response = self.sm_client.get_secret_value(
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
        file_obj: IO[bytes],
        service_account_info: dict
    ) -> Tuple[int, int]:
        credentials = service_account.Credentials.from_service_account_info(info=service_account_info)
        bq_client = bigquery.Client(credentials=credentials)

        destination = f"{dataset_id}.{table_id}"
        previous_rows = bq_client.get_table(table=destination).num_rows
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
        return previous_rows, current_rows


def lambda_handler(event, context) -> dict:
    if endpoint == "localstack":
        print("Start Testing with Localstack")
        s3_client = session.resource(
            service_name="s3",
            endpoint_url=s3_endpoint_url,
            config=Config()
        )
        sm_client = session.resource(
            service_name="secretsmanager",
            endpoint_url=sm_endpoint_url,
            config=Config()
        )
    else:
        s3_client = session.resource(service_name="s3")
        sm_client = session.resource(service_name="secretsmanager", region_name=aws_region)

    processor = LambdaProcessor(
        event=event,
        context=context,
        s3_client=s3_client,
        sm_client=sm_client,
        gcp_sa_secret_name=gcp_sa_secret_name

    )
    return processor.main()
