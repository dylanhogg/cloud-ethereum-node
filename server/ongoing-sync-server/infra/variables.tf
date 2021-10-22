variable "aws_profile" {
  type=string
}

variable "region" {
  type=string
}

variable "availability_zone" {
  type=string
}

variable "ongoing_sync_server_ami" {
  type=string
}

variable "ongoing_sync_server_instance_type" {
  type=string
}

variable "ongoing_sync_server_user_data_file" {
  type=string
}

variable "local_public_ip4_address" {
  type=string
}

variable "common_tags" { }
