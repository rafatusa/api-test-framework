output "instance_ip" {
  description = "Public Elastic IP of the application server."
  value       = aws_eip.app.public_ip
}
