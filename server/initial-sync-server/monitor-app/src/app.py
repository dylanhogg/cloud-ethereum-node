import os
import boto3
from library import ebs


def main():
    region_name = os.environ.get("AWS_REGION")
    assert region_name is not None, "AWS_REGION is not set"

    az_name = os.environ.get("AWS_AZ")
    assert az_name is not None, "AWS_AZ is not set"

    ec2_client = boto3.client('ec2', region_name=region_name)
    dry_run = False
    device = "/dev/xvdf"
    instance_id = "i-03b86bb25e45abf25"  # TODO
    size_gb = 2

    success = ebs.create_and_attach_volume(ec2_client, az_name, dry_run, device, instance_id, size_gb)
    if success:
        print("Yay!")
    else:
        print("Boo :(")


if __name__ == "__main__":
    main()
