import os
import time
import math
import boto3
from loguru import logger
from library import ebs, ec2, ssh, geth_status


def _temp_run(instance_dns, cmd):
    logger.info(f"Running: {cmd}")
    res = ssh._run(instance_dns, cmd)
    if len(res) > 0:
        logger.info(res)


def _process_completed_sync(instance_dns, status, ec2_client, data_dir, az_name, instance_id, ebs_factor=1.2):
    logger.info(f"Started processing completed sync with status of '{status}'...")

    # if status == geth_status.GethStatusEnum.stopped_success:
    if status == geth_status.GethStatusEnum.stopped_success or True:  # TEMP testing
        datadir_size_mb = ssh.geth_du(instance_dns, data_dir)
        assert datadir_size_mb > 0
        datadir_size_gb = datadir_size_mb/1.024e+6  # TODO: GiB vs GB
        logger.info(f"Size of datadir is {datadir_size_gb:.2f}GB")

        ebs_size_gb = int(math.ceil(datadir_size_gb * ebs_factor / 10.0)) * 10  # Round up nearest 10GB
        logger.info(f"Calc size of new EBS is {ebs_size_gb:.2f}GB (x{ebs_factor:.2f}")

        # TODO: review device
        # TODO: check if created already?
        # Create and attach EBS volume to instance
        ebs_success = ebs.create_and_attach_volume(ec2_client, az_name, instance_id, device="/dev/xvdf", size_gb=ebs_size_gb)
        assert ebs_success

        # TODO: format and mount attached EBS
        _temp_run(instance_dns, cmd="sudo mkdir /mnt/ebs_export/")
        _temp_run(instance_dns, cmd="sudo mkfs -t ext4 /dev/xvdf")
        _temp_run(instance_dns, cmd="sudo mount -t ext4 /dev/xvdf /mnt/ebs_export/")
        _temp_run(instance_dns, cmd="sudo mkdir /mnt/ebs_export/ethereum")
        _temp_run(instance_dns, cmd="sudo chown ec2-user:ec2-user /mnt/ebs_export/ethereum")

        # TODO: sanity check free space on ebs_export copy datadir

        # TODO: copy data
        _temp_run(instance_dns, cmd="cp --recursive /mnt/ebs/ethereum/* /mnt/ebs_export/ethereum/")

        # TODO: verify datadir

        # TODO: umount and then aws detach ebs
        _temp_run(instance_dns, cmd="sudo umount /mnt/ebs_export")

        # TODO: terminate initial sync server
        ec2.terminate_ec2_instance(ec2_client, instance_id)

        return True
    else:
        logger.info("Finished with errors")
        return False


def _wait_for_sync_completion(instance_dns, instance_type, datadir_mount, data_dir, interrupt_avail_pct=3.0, status_interval_secs=10):
    logger.info(f"Waiting for sync to complete, this will take quite some time...")

    status_count = 0
    while True:
        status_count += 1
        status, avail_pct, detail = geth_status.status(instance_dns, datadir_mount, data_dir)
        logger.info(f"\nGETH STATUS #{status_count} [{instance_type}] ({avail_pct:.2f}% available):\n"
                    + "\n".join(detail))

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


def manage_initial_sync_server(ec2_client, az_name, data_dir):
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
    datadir_mount = "/mnt/ebs"  # i3
    if instance_type.startswith("t4g"):
        datadir_mount = "/"  # t4g
    logger.info(f"datadir_mount = {datadir_mount} for {instance_type}")

    version = ssh.geth_version(instance_dns)
    if version != "1.10.9-stable":
        logger.warning(f"App tested with geth '1.10.9-stable' and your server is running '{version}'")

    status, avail_pct, detail = \
        _wait_for_sync_completion(instance_dns, instance_type, datadir_mount, data_dir)

    success = \
        _process_completed_sync(instance_dns, status, ec2_client, data_dir, az_name, instance_id)

    logger.info(f"Finished, success = {success}")


def main():
    region_name = os.environ.get("AWS_REGION")
    az_name = os.environ.get("AWS_AZ")
    assert region_name is not None, "AWS_REGION environ is not set"
    assert az_name is not None, "AWS_AZ environ is not set"
    ec2_client = boto3.client("ec2", region_name)

    data_dir = "/mnt/ebs/ethereum"

    manage_initial_sync_server(ec2_client, az_name, data_dir)


if __name__ == "__main__":
    main()
