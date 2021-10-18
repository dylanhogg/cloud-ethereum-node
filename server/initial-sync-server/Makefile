.EXPORT_ALL_VARIABLES:
APP_NAME=cloud-ethereum-node
AWS_PROFILE=prd-non-tf-905234897161
AWS_ACCOUNT_ID=905234897161
AWS_REGION=us-east-1
AWS_AZ=us-east-1b
PUBLIC_DNS=`cd infra; terraform output -raw public_dns`
EC2_INSTANCE_ID=`cd infra; terraform output -raw ec2_instance_id`
EBS_VOLUME_ID=cloud-ethereum-node-volume
ETH_DATA_DIR=/home/ec2-user/ethereum
# ETH_DATA_DIR=/mnt/nvm/ethereum

## Create public/private ssh keys
ssh-keygen:
	mkdir keys | true
	ssh-keygen -t rsa -b 4096 -N '' -f ./keys/id_rsa
	chmod 400 ./keys/id_rsa

# ------------------------------------------------------------------------
## ssh
ssh:
	ssh -i "./keys/id_rsa" ec2-user@${PUBLIC_DNS}

## ssh-cmd-disk
ssh-cmd-disk:
	@echo "Chaindata usage:"
	ssh -i "./keys/id_rsa" ec2-user@${PUBLIC_DNS} "du ${ETH_DATA_DIR} -h"
	@echo "Free space:"
	ssh -i "./keys/id_rsa" ec2-user@${PUBLIC_DNS} "df -h"

## ssh-cmd-geth
ssh-cmd-geth:
	@echo "geth status:"
	ssh -i "./keys/id_rsa" ec2-user@${PUBLIC_DNS} "/home/ec2-user/geth attach ipc:${ETH_DATA_DIR}/geth.ipc --exec eth.syncing"
	ssh -i "./keys/id_rsa" ec2-user@${PUBLIC_DNS} "/home/ec2-user/geth attach ipc:${ETH_DATA_DIR}/geth.ipc --exec 'eth.syncing.highestBlock - eth.syncing.currentBlock'"

## ssh-cmd-geth-logs
ssh-cmd-geth-logs:
	@echo "geth logs:"
	ssh -i "./keys/id_rsa" ec2-user@${PUBLIC_DNS} "tail -n20 /home/ec2-user/geth_nohup.out"

# ------------------------------------------------------------------------
# AWS CLI

aws-create-volume:
	aws ec2 create-volume \
	    --volume-type gp2 \
	    --size 2 \
	    --availability-zone ${AWS_AZ} \
	    --tag-specifications 'ResourceType=volume,Tags=[{Key=app_name,Value=${APP_NAME}},{Key=volume_id,Value=${EBS_VOLUME_ID}}]'

	VOLUME_ID=`aws ec2 describe-volumes --query Volumes[*].[VolumeId] --filters Name=tag-value,Values=${EBS_VOLUME_ID} --output text`; \
	echo $${VOLUME_ID}; \
	aws ec2 attach-volume --volume-id $${VOLUME_ID} --instance-id ${EC2_INSTANCE_ID} --device /dev/xvdf

aws-delete-volume:
	VOLUME_ID=`aws ec2 describe-volumes --query Volumes[*].[VolumeId] --filters Name=tag-value,Values=${EBS_VOLUME_ID} --output text`; \
	echo $${VOLUME_ID}; \
	aws ec2 detach-volume --volume-id $${VOLUME_ID}

	# TODO: handle An error occurred (VolumeInUse) when calling the DeleteVolume operation
# 	VOLUME_ID=`aws ec2 describe-volumes --query Volumes[*].[VolumeId] --filters Name=tag-value,Values=${EBS_VOLUME_ID} --output text`; \
# 	echo $${VOLUME_ID}; \
# 	aws ec2 delete-volume --volume-id $${VOLUME_ID}

# ------------------------------------------------------------------------
# Terraform

## TF init
tf-init:
	cd infra; terraform init -var-file=variables.tfvars; cd -

## TF validate
tf-validate:
	cd infra; terraform validate; cd -

## TF plan
tf-plan:
	cd infra; terraform plan -var-file=variables.tfvars; cd -

## TF apply
tf-apply: tf-plan
	cd infra; terraform apply -var-file=variables.tfvars -auto-approve; cd -
	# cd infra; terraform apply -var-file=variables.tfvars; cd -

## TF output
tf-output:
	cd infra; terraform output; cd -

## TF destroy
tf-destroy:
	cd infra; terraform destroy -var-file=variables.tfvars -auto-approve; cd -
	# cd infra; terraform destroy -var-file=variables.tfvars; cd -


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
