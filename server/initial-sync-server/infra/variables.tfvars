aws_profile="prd-non-tf-905234897161"
region="us-east-1"
availability_zone="us-east-1b"

# x86 i3.xlarge (also change user_data.sh)
# initial_sync_server_ami="ami-02e136e904f3da870"  # Amazon Linux 2 AMI (HVM), SSD Volume Type (64-bit x86)
# initial_sync_server_instance_type="i3.xlarge"    # @ $0.312/hr, 64-bit x86?, 4 vCPU, 30.5 GiB, 1x950 NVMe SSD, Up to 10 Gigabit
# initial_sync_server_user_data_file="scripts/user_data_amd64_i3.sh"

# ARM t4g.medium (also change user_data.sh)
initial_sync_server_ami="ami-0e341fcaad89c3650"  # Amazon Linux 2 AMI (HVM), SSD Volume Type (64-bit Arm)
initial_sync_server_instance_type="t4g.medium"   # $0.0336/hr, 64-bit Arm, 2 vCPU, 4 GiB, EBS Only, Up to 5 Gigabit
initial_sync_server_user_data_file="scripts/user_data_arm_t4g.sh"

common_tags = {
  tag_version = "1.0"
  deployment  = "tf"
  app_name    = "cloud-ethereum-node"
  env         = "prd"
}