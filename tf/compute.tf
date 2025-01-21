#* Define the EC2 instance
resource "aws_instance" "app_server" {
  ami                         = "ami-0030d50a3ce637c3a"
  instance_type               = "t4g.small"
  subnet_id                   = aws_subnet.public_a.id
  key_name                    = "GopherMapsSSH"
  vpc_security_group_ids      = [aws_security_group.backend.id]
  associate_public_ip_address = true  # Needs an IPv4 address for CodeDeploy

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
  }

  iam_instance_profile = "CodeDeploy-EC2-Instance_profile"
  user_data            = file("ec2-setup.sh")

  tags = {
    Name        = "gophermaps-backend"
    Environment = "production"
    Application = "gophermaps" # For CodeDeploy to identify the instance
  }
}
