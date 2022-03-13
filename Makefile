include .env

dryrun-dms-endpoint-resources:
	@sam build -t templates/dms-endpoints/root.yaml
	@sam deploy -t templates/dms-endpoints/root.yaml --no-execute-changeset

deploy-dms-endpoint-resources:
	@sam build -t templates/dms-endpoints/root.yaml
	@sam deploy -t templates/dms-endpoints/root.yaml --no-confirm-changeset --no-fail-on-empty-changeset

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
			"DataFormat": "parquet", \
			"CompressionType": "GZIP", \
			"EncodingType": "plain-dictionary", \
			"DictPageSizeLimit": 3072000, \
			"EnableStatistics": false \
		}' \
		--no-cli-pager \
		--output json

deploy-dms-resources:
	@sam build -t templates/dms/dms.yaml
