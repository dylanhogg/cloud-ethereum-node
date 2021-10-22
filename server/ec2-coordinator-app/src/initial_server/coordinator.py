import time
import initial_server
from loguru import logger
from library import ec2, ssh


def start(ec2_client, az_name, data_dir, debug_run, terminate_instance):
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

    status, instance_type, avail_pct, detail, perc_block = \
        initial_server.wait_for_sync_completion.wait(instance_dns, instance_type, datadir_mount, data_dir, debug_run)

    success = \
        initial_server.process_completed_sync.process(instance_dns, status, ec2_client, data_dir, az_name, instance_id,
                                                      instance_type, version, perc_block, debug_run, terminate_instance)

    logger.info(f"Finished initial server coordination with success = {success}")
