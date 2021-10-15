resource "aws_security_group" "initial_sync_server_sg" {
  name              = "initial_sync_server"
  description       = "initial_sync_server"
  vpc_id            = data.aws_vpc.default_vpc.id
  tags              = var.common_tags

  ingress {
    # ssh
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    cidr_blocks     = ["0.0.0.0/0"]  # TODO: lockdown to a your ip address
  }

  egress {
    # Download geth binary
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    cidr_blocks     = ["0.0.0.0/0"]
  }

  egress {
    # geth listener default
    from_port       = 30303
    to_port         = 30303
    protocol        = "tcp"
    cidr_blocks     = ["0.0.0.0/0"]
  }

  egress {
    # geth discovery default
    from_port       = 30303
    to_port         = 30303
    protocol        = "udp"
    cidr_blocks     = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "initial_sync_server_key" {
  key_name          = "initial_sync_server_key"
  public_key        = file("../keys/id_rsa.pub")
  tags              = var.common_tags
}

resource "aws_instance" "initial_sync_server" {
  ami               = var.initial_sync_server_ami
  instance_type     = var.initial_sync_server_instance_type
  availability_zone = var.availability_zone
  vpc_security_group_ids = [aws_security_group.initial_sync_server_sg.id]

  associate_public_ip_address = true
  key_name = aws_key_pair.initial_sync_server_key.key_name

  user_data         = file("scripts/initial_sync_server_userdata.sh")

  tags              = var.common_tags
}
