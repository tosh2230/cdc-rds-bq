TEMPLATE_FILE=

include .env

dryrun:
	@sam build -t ${TEMPLATE_FILE}
	@sam deploy -t ${TEMPLATE_FILE} --no-execute-changeset

deploy:
	@sam build -t ${TEMPLATE_FILE}
	@sam deploy -t ${TEMPLATE_FILE} --no-confirm-changeset --no-fail-on-empty-changeset

setup:
	@make deploy TEMPLATE_FILE=templates/vpc_resources/root.yaml
	@make deploy TEMPLATE_FILE=templates/s3/s3.yaml

# https://docs.aws.amazon.com/cli/latest/reference/dms/create-endpoint.html
create-dms-endpoint-mysql:
	aws dms create-endpoint \
		--endpoint-identifier source-endpoint-mysql \
		--engine-name mysql \
		--endpoint-type source \
		--my-sql-settings '{ \
			"EventsPollInterval": 5, \
			"ServerTimezone": "UTC", \
			"SecretsManagerAccessRoleArn": "$(RDS_SECRETS_ROLE_ARN)", \
			"SecretsManagerSecretId": "$(RDS_SECRETS_ARN)" \
		}' \
		--no-cli-pager \
		--output json

# https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.S3.html#CHAP_Target.S3.Configuring
create-dms-endpoint-s3:
	aws dms create-endpoint \
		--endpoint-identifier target-endpoint-s3 \
		--engine-name s3 \
		--endpoint-type target \
		--s3-settings '{ \
			"ServiceAccessRoleArn": "$(S3_ENDPOINT_ROLE_ARN)", \
			"BucketName": "$(S3_BUCKET_NAME)", \
			"EncryptionMode": "SSE_S3", \
			"DataFormat": "parquet", \
			"ParquetVersion": "PARQUET_2_0", \
			"CompressionType": "GZIP", \
			"EnableStatistics": true, \
			"EncodingType": "rle-dictionary", \
			"CdcMaxBatchInterval": 60, \
			"DataPageSize": 1024000, \
			"RowGroupLength": 10024, \
			"DictPageSizeLimit": 1024000, \
			"AddColumnName": true, \
			"TimestampColumnName": "CdcTimestamp", \
			"DatePartitionEnabled": true, \
			"DatePartitionSequence": "YYYYMMDD", \
			"DatePartitionDelimiter": "SLASH" \
		}' \
		--no-cli-pager \
		--output json

deploy-dms-task:
	@make deploy TEMPLATE_FILE=templates/dms_task/dms_task.yaml
