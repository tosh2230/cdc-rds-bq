TEMPLATE_FILE=

include .env

dryrun:
	@sam build -t ${TEMPLATE_FILE}
	@sam deploy -t ${TEMPLATE_FILE} --no-execute-changeset

deploy:
	@sam build -t ${TEMPLATE_FILE}
	@sam deploy -t ${TEMPLATE_FILE} --no-confirm-changeset --no-fail-on-empty-changeset

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
			"CompressionType": "GZIP", \
			"EncodingType": "plain-dictionary", \
			"DictPageSizeLimit": 3072000, \
			"EnableStatistics": false \
		}' \
		--no-cli-pager \
		--output json
