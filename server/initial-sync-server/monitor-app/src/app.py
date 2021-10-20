import os
import time
import boto3
from loguru import logger
from library import ebs, ec2, ssh, geth_status


def _wait_for_sync_completion(instance_dns, datadir_mount, data_dir, interrupt_avail_pct=3.0, status_interval_secs=10):
    status_count = 0
    while True:
        status_count += 1
        status, avail_pct, detail = geth_status.status(instance_dns, datadir_mount, data_dir)
        logger.info(f"\nGETH STATUS #{status_count} ({avail_pct:.2f}% available):\n" + "\n".join(detail))

        if status != geth_status.GethStatusEnum.running:
            logger.info(f"Exiting monitoring due to geth status {status}")
            break

        if avail_pct < interrupt_avail_pct:
            # TODO: review
            pid = ssh.geth_sigint(instance_dns)
            logger.info("Disk free:\n" + ssh.df(instance_dns, human=True))
            logger.info("Disk usage:\n" + ssh.du(instance_dns, human=True))
            logger.error(f"Interrupting geth process {pid} due to only {avail_pct:.2f}% avaiable on volume")
            break

        time.sleep(status_interval_secs)

    return status, avail_pct, detail


def _process_completed_sync(instance_dns, status, ec2_client, data_dir, az_name, instance_id):
    if status == geth_status.GethStatusEnum.stopped_success:
        # TODO: get datadir size + ~50GB
        data_dir_size = ssh.geth_du(instance_dns, data_dir)

        size_mb = ssh.geth_du(instance_dns, data_dir)
        assert size_mb > 0
        size_gb = size_mb/1.024e+6  # TODO: GiB vs GB
        logger.info(f"Size of datadir is {size_gb:,2}GB")

        # TODO: review device
        # Create and attach EBS volume to instance
        ebs_success = ebs.create_and_attach_volume(ec2_client, az_name, instance_id, device="/dev/xvdf", size_gb=3)
        assert ebs_success

        return True

        # TODO: copy datadir
        # TODO: verify datadir
        # TODO: detach ebs
        # TODO: terminate initial sync server
    else:
        logger.info("Finished with errors")
        return False


def manage_initial_sync_server(ec2_client, az_name):
    ec2_tag_name = "ethereum-initial-sync-server"
    success, instance_id, instance_ip, instance_dns, instance_type = \
        ec2.find_ec2_instance(ec2_client, tag_name=ec2_tag_name)

    if not success:
        logger.info(f"Exiting app since no instance found with tag '{ec2_tag_name}'")
        return

    logger.info(f"Found EC2 InstanceId: {instance_id}, {instance_ip}, {instance_dns}, {instance_type}")

    data_dir = "/mnt/ebs/ethereum"
    datadir_mount = "/mnt/ebs"  # i3
    if instance_type.startswith("t4g"):
        datadir_mount = "/"  # t4g

    version = ssh.geth_version(instance_dns)
    if version != "1.10.9-stable":
        logger.warning(f"App tested with geth '1.10.9-stable' and your server is running '{version}'")

    status, avail_pct, detail = \
        _wait_for_sync_completion(instance_dns, datadir_mount, data_dir)

    success = \
        _process_completed_sync(instance_dns, status, ec2_client, data_dir, az_name, instance_id)

    logger.info(f"Finished, success = {success}")


def main():
    region_name = os.environ.get("AWS_REGION")
    az_name = os.environ.get("AWS_AZ")
    assert region_name is not None, "AWS_REGION environ is not set"
    assert az_name is not None, "AWS_AZ environ is not set"
    ec2_client = boto3.client("ec2", region_name)

    manage_initial_sync_server(ec2_client, az_name)


if __name__ == "__main__":
    main()
