import os
import time
from loguru import logger
from library import ec2, ssh
from initial_server import wait_for_sync_completion, process_completed_sync


def start_app(ec2_client, az_name, data_dir, debug_run, terminate_instance):
    if debug_run:
        logger.error(f"debug_run set to True; will interrupt sync prematurely!")

    ec2_tag_name = "ethereum-initial-sync-server"

    success, instance_id, instance_ip, instance_dns, instance_type = \
        ec2.find_ec2_instance(ec2_client, tag_name=ec2_tag_name)

    while not success:
        logger.warning(f"No instance found with tag '{ec2_tag_name}. Pausing before trying again...'")
        time.sleep(30)
        success, instance_id, instance_ip, instance_dns, instance_type = \
            ec2.find_ec2_instance(ec2_client, tag_name=ec2_tag_name)

    logger.info(f"Found EC2 InstanceId: {instance_id}, {instance_ip}, {instance_dns}, {instance_type}")

    # TODO: handle datadir_mount better
    datadir_mount = "/mnt/sync"  # i3
    if instance_type.startswith("t4g"):
        datadir_mount = "/"  # t4g
    logger.info(f"datadir_mount = {datadir_mount} for {instance_type}")

    version = ssh.geth_version(instance_dns)
    logger.info(f"geth version '{version}'")
    expected_version = "1.10.9-stable"
    if version != expected_version:
        logger.warning(f"App tested with geth '{expected_version}' and your server is running '{version}'")

    status, instance_type, avail_pct, detail, perc_block, highest_block, current_block = \
        wait_for_sync_completion.wait(instance_dns, instance_type, datadir_mount, data_dir, debug_run)

    success = \
        process_completed_sync.process(instance_dns, status, ec2_client, data_dir, az_name, instance_id,
                                       instance_type, version, perc_block, highest_block, current_block,
                                       debug_run, terminate_instance)

    logger.info(f"Finished initial server coordination with success = {success}")


def main():
    region_name = os.environ.get("AWS_REGION")
    az_name = os.environ.get("AWS_AZ")
    assert region_name is not None, "AWS_REGION environ is not set"
    assert az_name is not None, "AWS_AZ environ is not set"

    ec2_client = ec2.get_client(region_name)
    data_dir = "/mnt/sync/ethereum"
    debug_run = True
    terminate_instance = True
    start_app(ec2_client, az_name, data_dir, debug_run, terminate_instance)


if __name__ == "__main__":
    main()
