TEMPLATE_FILE=

dryrun:
	@sam build -t ${TEMPLATE_FILE}
	@sam deploy --no-execute-changeset

deploy:
	@sam build -t ${TEMPLATE_FILE}
	@sam deploy --no-confirm-changeset --no-fail-on-empty-changeset

setup:
	@make deploy TEMPLATE_FILE=templates/s3/s3.yaml
	@make deploy TEMPLATE_FILE=templates/vpc_resources/root.yaml
	@make deploy TEMPLATE_FILE=templates/dms/dms.yaml
	@make deploy TEMPLATE_FILE=templates/ecr/ecr.yaml
	@make deploy TEMPLATE_FILE=templates/lambda/lambda.yaml
