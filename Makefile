include .env

dryrun-endpoint-resources:
	@sam build -t templates/endpoint-resources/root.yaml
	@sam deploy -t templates/endpoint-resources/root.yaml --no-execute-changeset
deploy-endpoint-resources:
	@sam build -t templates/endpoint-resources/root.yaml
	@sam deploy -t templates/endpoint-resources/root.yaml --no-confirm-changeset --no-fail-on-empty-changeset

create-mysql-endpoint:
	aws dms create-endpoint \
		--endpoint-identifier source-endpoint-mysql \
		--engine-name mysql \
		--endpoint-type source \
		--my-sql-settings '{ \
			"EventsPollInterval": 5, \
			"ServerTimezone": "UTC", \
			"SecretsManagerAccessRoleArn": "$(RDS_SECRETS_ROLE_ARN)", \
			"SecretsManagerSecretId": "$(RDS_SECRETS_ARN)" \
		}'

create-s3-endpoint:
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
		}'
