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


# TODO make the subnets public by adding routes to the IGW
#* Create two public subnets for the VPC with no IPv4
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.gophermaps-vpc.id
  cidr_block              = "1.0.0.0/27" # First half of the VPC CIDR block
  ipv6_cidr_block         = cidrsubnet(aws_vpc.gophermaps-vpc.ipv6_cidr_block, 8, 0)
  map_public_ip_on_launch = false
  availability_zone       = "us-east-2a"
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.gophermaps-vpc.id
  cidr_block              = "1.0.0.32/27" # Second half of the VPC CIDR block
  ipv6_cidr_block         = cidrsubnet(aws_vpc.gophermaps-vpc.ipv6_cidr_block, 8, 1)
  map_public_ip_on_launch = false
  availability_zone       = "us-east-2b"
}

#* Create a security group for the load balancer
# - Allow inbound HTTPS connections
# - Allow outbound traffic to anywhere in the VPC

#* Create a security group for the backend
# - Allow inbound SSH connections
# - Allow inbound HTTP connections from the load balancer
# - Allow outbound connections to Neo4j
# - Allow outbound HTTPS connections for codedeploy
