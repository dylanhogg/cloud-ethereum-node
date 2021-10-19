resource "aws_security_group" "initial_sync_server_sg" {
  name              = "ethereum_initial_sync_server"
  description       = "initial_sync_server"
  vpc_id            = data.aws_vpc.default_vpc.id
  tags              = merge(var.common_tags, { Name = "ethereum-initial-sync-server-sg" })

  ingress {
    # ssh
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    cidr_blocks     = ["${var.local_public_ip4_address}/32"]  # TODO: review
  }

  ingress {
    # rcp server http.port
    from_port       = 8545
    to_port         = 8545
    protocol        = "tcp"
    cidr_blocks     = ["${var.local_public_ip4_address}/32"]  # TODO: review
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
  key_name          = "ethereum_initial_sync_server_key"
  public_key        = file("../keys/id_rsa.pub")
  tags              = merge(var.common_tags, { Name = "ethereum-initial-sync-server-key" })
}

resource "aws_instance" "initial_sync_server" {
  ami               = var.initial_sync_server_ami
  instance_type     = var.initial_sync_server_instance_type
  availability_zone = var.availability_zone
  vpc_security_group_ids = [aws_security_group.initial_sync_server_sg.id]

  associate_public_ip_address = true
  key_name          = aws_key_pair.initial_sync_server_key.key_name
  user_data         = file(var.initial_sync_server_user_data_file)

  tags              = merge(var.common_tags, { Name = "ethereum-initial-sync-server" })
}
