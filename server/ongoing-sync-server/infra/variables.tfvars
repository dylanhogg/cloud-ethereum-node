aws_profile="prd-non-tf-905234897161"
region="us-east-1"
availability_zone="us-east-1b"
local_public_ip4_address="101.184.148.175"  # TODO: get dynamically?

# ARM t4g.medium
ongoing_sync_server_ami="ami-0e341fcaad89c3650"  # Amazon Linux 2 AMI (HVM), SSD Volume Type (64-bit Arm)
ongoing_sync_server_instance_type="t4g.medium"   # $0.0336/hr, 64-bit Arm, 2 vCPU, 4 GiB, EBS Only, Up to 5 Gigabit
ongoing_sync_server_user_data_file="scripts/user_data_arm_t4g.sh"

common_tags = {
  tag_version = "1.0"
  deployment  = "tf"
  app_name    = "cloud-ethereum-node"
  app_server  = "ongoing-sync-server"
  env         = "prd"
}
