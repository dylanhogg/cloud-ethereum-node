import os
import time
from loguru import logger
from library import ec2, ssh
from ongoing_server import initialise_ongoing_instance


def start_app(ec2_client, ec2_resource, az_name, data_dir, debug_run):
    if debug_run:
        logger.error(f"debug_run set to True;")

    ec2_tag_name = "ethereum-ongoing-sync-server"

    success, instance_id, instance_ip, instance_dns, instance_type = \
        ec2.find_ec2_instance(ec2_client, tag_name=ec2_tag_name)

    while not success:
        logger.warning(f"No instance found with tag '{ec2_tag_name}. Pausing before trying again...'")
        time.sleep(30)
        success, instance_id, instance_ip, instance_dns, instance_type = \
            ec2.find_ec2_instance(ec2_client, tag_name=ec2_tag_name)

    logger.info(f"Found EC2 InstanceId: {instance_id}, {instance_ip}, {instance_dns}, {instance_type}")

    datadir_mount = "/"  # t4g
    if not instance_type.startswith("t4g"):
        raise RuntimeError("Only tested on t4g instance types.")

    logger.info(f"datadir_mount = {datadir_mount} for {instance_type}")

    version = ssh.geth_version(instance_dns)
    logger.info(f"geth version '{version}'")
    expected_version = "1.10.9-stable"
    if version != expected_version:
        logger.warning(f"App tested with geth '{expected_version}' and your server is running '{version}'")

    # Initialise ongoing instance
    initialise_instance.start(ec2_resource, az_name, data_dir, debug_run)

    logger.info(f"Finished ongoing server coordination with success = {success}")


def testing(ec2_client, ec2_resource, az_name, data_dir, debug_run):
    # Initialise ongoing instance
    initialise_ongoing_instance.start(ec2_client, ec2_resource, az_name, data_dir, debug_run)


def main():
    region_name = os.environ.get("AWS_REGION")
    az_name = os.environ.get("AWS_AZ")
    assert region_name is not None, "AWS_REGION environ is not set"
    assert az_name is not None, "AWS_AZ environ is not set"

    ec2_client = ec2.get_client(region_name)
    ec2_resource = ec2.get_resource(region_name)
    data_dir = "/mnt/sync/ethereum"
    debug_run = True
    # start_app(ec2_client, az_name, data_dir, debug_run)
    testing(ec2_client, ec2_resource, az_name, data_dir, debug_run)


if __name__ == "__main__":
    main()
