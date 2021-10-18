output "private_ip" {
  description = "The public ip for initial_sync_server"
  value       = aws_instance.initial_sync_server.private_ip
}

output "public_ip" {
  description       = "The public ip for initial_sync_server"
  value             = aws_instance.initial_sync_server.public_ip
}

output "private_dns" {
  description = "The private DNS for initial_sync_server"
  value       = aws_instance.initial_sync_server.private_dns
}

output "public_dns" {
  description = "The public DNS for initial_sync_server"
  value       = aws_instance.initial_sync_server.public_dns
}

output "ec2_instance_id" {
  description = "The ec2 instance for initial_sync_server"
  value       = aws_instance.initial_sync_server.id
}
