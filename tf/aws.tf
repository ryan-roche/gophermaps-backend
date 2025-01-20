terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

#! You'll need to change the "profile" key to match whatever your AWS CLI profile is called on your machine
provider "aws" {
  region = "us-east-2"
  profile = "SocialCoding"
}
