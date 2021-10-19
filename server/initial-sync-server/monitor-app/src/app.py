import os
import boto3
from loguru import logger
from library import ebs, ec2, ssh, geth


def manage_initial_sync_server(ec2_client):
    instance_id, instance_ip, instance_dns = ec2.find_ec2_instance(ec2_client, tag_name="ethereum-initial-sync-server")
    logger.info(f"Found EC2 InstanceId: {instance_id}, {instance_ip}, {instance_dns}")

    # pid = ssh.geth_pid(instance_dns)
    # logger.info(f"geth_pid = {pid}")
    # if pid is None:
    #     logger.warning(f"geth not running, it may have finished or not started.")

    status, detail = geth.status(instance_dns)
    logger.info(f"\nGETH STATUS:\n{status}\n" + "\n".join(detail))

    # logs = ssh.geth_logs(instance_dns, 10)
    # logger.info(f"geth_logs = {logs}")

    # df = ssh.df(instance_dns)
    # logger.info(f"df = {df}")
    #
    # du = ssh.geth_du(instance_dns)
    # logger.info(f"du = {du}")

    # ps = ssh.ps(instance_dns)
    # logger.info(f"ps = {ps}")

    # TODO: call rcp server http.port 8545 directly with e.g. eth.syncing

    # Create and attach EBS volume to instance
    # ebs_success = ebs.create_and_attach_volume(ec2_client, az_name, instance_id, device="/dev/xvdf", size_gb=1)
    # assert ebs_success


def main():
    region_name = os.environ.get("AWS_REGION")
    az_name = os.environ.get("AWS_AZ")
    assert region_name is not None, "AWS_REGION environ is not set"
    assert az_name is not None, "AWS_AZ environ is not set"
    ec2_client = boto3.client("ec2", region_name)

    manage_initial_sync_server(ec2_client)


if __name__ == "__main__":
    main()
