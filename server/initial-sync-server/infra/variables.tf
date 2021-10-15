variable "aws_profile" {
  type=string
}

variable "region" {
  type=string
}

variable "availability_zone" {
  type=string
}

variable "initial_sync_server_ami" {
  type=string
}

variable "initial_sync_server_instance_type" {
  type=string
}

variable "common_tags" { }
