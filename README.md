# Cloud Ethereum Node
Deploy and run an Ethereum node on AWS

# Steps

## Prerequisites

1) Have an [AWS account](https://portal.aws.amazon.com/billing/signup#/start)
2) [AWS CLI installed and configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)
3) [Terraform CLI installed](https://www.terraform.io/downloads)


## Create Initial Sync Server on large EC2 (temporary instance)

1) Review variables at `server/initial-sync-server/infra/variables.tfvars`:
   1) Set `local_public_ip4_address` to your IPv4 address for ssh access
   2) Also review AWS region/az and profile name
2) Review Geth install version at `server/initial-sync-server/infra/scripts/user_data_amd64_i3.sh`
3) Ensure working directory: `cd server/initial-sync-server`
4) Create EC2 ssh key: `make ssh-keygen`
5) Init Terraform: `make tf-init`
6) Plan Terraform: `make tf-plan`
7) Apply Terraform: `make tf-apply`
8) Optional: Once instance is running you can ssh in with `make ssh`


## Create Ongoing Sync Server on small EC2 (permanent ongoing instance)

1) Review TF variables at `server/initial-sync-server/infra/variables.tfvars`:
   1) Set `local_public_ip4_address` to your IPv4 address for ssh access
   2) Also review AWS region/az and profile name
2) Review Geth install version at `server/ongoing-sync-server/infra/scripts/user_data_arm_t4g.sh`
3) Ensure working diretory: `cd server/ongoing-sync-server`
4) Create EC2 ssh key: `make ssh-keygen`
5) Init Terraform: `make tf-init`
6) Plan Terraform: `make tf-plan`
7) Apply Terraform: `make tf-apply`
8) Optional: Once instance is running you can ssh in with `make ssh`


## Run Initial EC2 Coordinator App to transition EBS from large to small EC2 instance when complete 

1) `cd server/ec2-coordinator-app`
2) Run script to monitor `make initial_server_app`
3) The script will wait until the machine is running and initialised
4) Once initialised the scipt will monitor geth syncing progress, free disk space and other metrics
5) Once progress is above a threshold, the EBS volume will be detached and the large instance terminated
6) The volume is then attached to the small ongoing instance and syncing resumed
7) Find EBS volume with name `ethereum-initial-sync-server-ebs-export` and tags with meta-data


## Run Ongoing EC2 Coordinator App

1) TODO
2) 