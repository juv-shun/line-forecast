terraform {
  required_version = ">= 0.11.5"

  backend "s3" {
    bucket  = "juv-shun.tfstate"
    key     = "forecast/tfstate.tf"
    profile = "default"
    region  = "ap-northeast-1"
  }
}

provider "aws" {
  region                  = "ap-northeast-1"
  profile                 = "default"
  shared_credentials_file = "~/.aws/credentials"
}
