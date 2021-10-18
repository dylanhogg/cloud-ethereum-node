import os
import subprocess
import boto3
from loguru import logger
from library import ebs, ec2


def main():
    region_name = os.environ.get("AWS_REGION")
    az_name = os.environ.get("AWS_AZ")
    assert region_name is not None, "AWS_REGION environ is not set"
    assert az_name is not None, "AWS_AZ environ is not set"
    ec2_client = boto3.client('ec2', region_name)

    # TODO: also get public_dns & public_ip4
    instance_id = ec2.find_ec2_instance(ec2_client, ec2_name="ethereum-initial-sync-server")

    # Create and attach EBS volume to instance
    ebs_success = ebs.create_and_attach_volume(ec2_client, az_name, instance_id, device="/dev/xvdf", size_gb=1)
    assert ebs_success

    # Execute remote ssh command
    public_dns = "ec2-34-227-194-126.compute-1.amazonaws.com"
    public_ip = "34.227.194.126"
    ssh_cmd = "du /home/ec2-user/ethereum -h"
    ssh_wrapper_cmd = f'ssh -o "StrictHostKeyChecking no" -i "../keys/id_rsa" ec2-user@{public_dns} "{ssh_cmd}"'
    p = subprocess.Popen(ssh_wrapper_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    logger.info(f"ssh resp:\n{p[0].decode()}")

    # TODO: call rcp server http.port 8545 directly with e.g. eth.syncing


if __name__ == "__main__":
    main()
