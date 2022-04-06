import os
from boto3 import Session
from boto3.resources.base import ServiceResource
from botocore.config import Config
from processor import LambdaProcessor

endpoint = os.environ["ENDPOINT"]
s3_endpoint_url = os.environ["S3_ENDPOINT_URL"]
sm_endpoint_url = os.environ["SECRETS_MANAGER_ENDPOINT_URL"]
aws_region = os.environ["AWS_REGION"]
gcp_sa_secret_name = os.environ["GCP_SA_SECRET_NAME"]

session = Session()
s3_client: ServiceResource
sm_client: ServiceResource

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

def lambda_handler(event, context) -> dict:
    processor = LambdaProcessor(
        event=event,
        context=context,
        s3_client=s3_client,
        sm_client=sm_client,
        gcp_sa_secret_name=gcp_sa_secret_name

    )
    return processor.main()
