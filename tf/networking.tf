#* Create a VPC for the backend and load balancer
resource "aws_vpc" "gophermaps-vpc" {
  cidr_block           = "1.0.0.0/26"
  enable_dns_support   = true
  enable_dns_hostnames = true

  # Enable IPv6
  assign_generated_ipv6_cidr_block = true

  tags = {
    Name = "GopherMaps-VPC"
  }
}

#* Add an internet gateway to the VPC
resource "aws_internet_gateway" "gophermaps-igw" {
  vpc_id = aws_vpc.gophermaps-vpc.id

  tags = {
    Name = "GopherMaps-VPC-igw"
  }
}


#* Create a route table for the public subnets to use
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.gophermaps-vpc.id

  # Route IPv4 traffic to the internet gateway
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gophermaps-igw.id
  }

  # Route IPv6 traffic to the internet gateway
  route {
    ipv6_cidr_block = "::/0"
    gateway_id      = aws_internet_gateway.gophermaps-igw.id
  }

  tags = {
    Name = "GopherMaps-public-rt"
  }
}

#* Create two public subnets for the VPC with no IPv4
resource "aws_subnet" "public_a" {
  vpc_id                          = aws_vpc.gophermaps-vpc.id
  cidr_block                      = "1.0.0.0/27"    # First half of the VPC CIDR block
  ipv6_cidr_block                 = cidrsubnet(aws_vpc.gophermaps-vpc.ipv6_cidr_block, 8, 0)
  assign_ipv6_address_on_creation = true
  map_public_ip_on_launch         = false   # Don't auto-assign public ipv4 addresses
  availability_zone               = "us-east-2a"
}

resource "aws_subnet" "public_b" {
  vpc_id                          = aws_vpc.gophermaps-vpc.id
  cidr_block                      = "1.0.0.32/27"   # Second half of the VPC CIDR block
  ipv6_cidr_block                 = cidrsubnet(aws_vpc.gophermaps-vpc.ipv6_cidr_block, 8, 1)
  assign_ipv6_address_on_creation = true
  map_public_ip_on_launch         = false   # Don't auto-assign public ipv4 addresses
  availability_zone               = "us-east-2b"
}

#* Associate the public routing table with the subnets
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

#* Create a security group for the load balancer
resource "aws_security_group" "lb" {
  name        = "gophermaps-lb-sg"
  description = "Security group for the load balancer"
  vpc_id      = aws_vpc.gophermaps-vpc.id

  # Allow inbound HTTPS traffic from anywhere
  ingress {
    description      = "HTTPS from anywhere"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # Allow all outbound traffic within the VPC
  egress {
    description      = "Outbound to VPC"
    from_port        = 0
    to_port          = 0
    protocol         = "-1" # All protocols
    cidr_blocks      = [aws_vpc.gophermaps-vpc.cidr_block]
    ipv6_cidr_blocks = [aws_vpc.gophermaps-vpc.ipv6_cidr_block]
  }

  tags = {
    Name = "GopherMaps-LB-SG"
  }
}

#* Create a security group for the backend
resource "aws_security_group" "backend" {
  name        = "gophermaps-backend-sg"
  description = "Security group for backend servers"
  vpc_id      = aws_vpc.gophermaps-vpc.id

  # Allow SSH from anywhere
  ingress {
    description      = "SSH from anywhere"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # Allow HTTP from within VPC only
  ingress {
    description      = "HTTP from VPC"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = [aws_vpc.gophermaps-vpc.cidr_block]
    ipv6_cidr_blocks = [aws_vpc.gophermaps-vpc.ipv6_cidr_block]
  }

  # Allow outbound HTTPS for CodeDeploy agent
  egress {
    description      = "HTTPS for CodeDeploy"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # Allow outbound TCP on port 7687 (neo4j bolt)
  egress {
    description      = "Custom TCP 7687"
    from_port        = 7687
    to_port          = 7687
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "GopherMaps-Backend-SG"
  }
}
