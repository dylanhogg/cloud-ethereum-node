import os
import time
import math
import boto3
from datetime import datetime
from loguru import logger
from library import ebs, ec2, ssh, geth_status


def _process_completed_sync(instance_dns, status, ec2_client, data_dir, az_name, instance_id, instance_type, version, perc_block, ebs_factor=1.2):
    logger.info(f"Started process completed sync. Status '{status}', >{perc_block:.2f}% block")

    # if status == geth_status.GethStatusEnum.stopped_success:
    if status == geth_status.GethStatusEnum.stopped_success or True:  # TEMP: for testing
        datadir_size_mb = ssh.geth_du(instance_dns, data_dir)
        assert datadir_size_mb > 0
        datadir_gb = datadir_size_mb/1.024e+6  # TODO: GiB vs GB
        logger.info(f"Size of datadir is {datadir_gb:.2f}GB")

        ebs_size_gb = int(math.ceil(datadir_gb * ebs_factor / 10.0)) * 10  # Round up nearest 10GB
        logger.info(f"Calc size of new EBS is {ebs_size_gb:.2f}GB (x{ebs_factor:.2f} rounded up to nearest 10GB)")
        logger.warning(f"Estimated cost for {ebs_size_gb:.2f}GB EBS is {(ebs_size_gb*0.1):.2f} USD/month "
                       f"(us-east-1, gp2, no snapshot, {ebs_size_gb:.2f}GB * 0.10 USD)")

        # TODO: review device
        # TODO: check if created already by tag

        ebs_device = "/dev/xvdf"  # TODO: review by instance type
        ebs_tags = [
            {"Key": "Name", "Value": "ethereum-initial-sync-server-ebs-export"},
            {"Key": "deployment", "Value": "boto"},
            {"Key": "app_name", "Value": "cloud-ethereum-node"},
            {"Key": "env", "Value": "prd"},
            {"Key": "meta_sync_date", "Value": datetime.now().replace(microsecond=0).isoformat()},
            {"Key": "meta_geth_status", "Value": status.name},
            {"Key": "meta_geth_perc_block", "Value": "{:.2f}%".format(perc_block)},
            {"Key": "meta_geth_version", "Value": version},
            {"Key": "meta_instance_id", "Value": instance_id},
            {"Key": "meta_instance_type", "Value": instance_type},
            {"Key": "meta_device", "Value": ebs_device},
            {"Key": "meta_data_dir", "Value": data_dir},
            {"Key": "meta_size_gb", "Value": "{:.2f}".format(ebs_size_gb)},
            {"Key": "meta_datadir_gb", "Value": "{:.2f}".format(datadir_gb)},
        ]

        # Create and attach EBS volume to instance
        ebs_success, volume_id = ebs.create_and_attach_volume(
            ec2_client, az_name, instance_id, device=ebs_device, size_gb=ebs_size_gb, tags=ebs_tags)
        if not ebs_success:
            raise RuntimeError(f"Failed to create/attach volume to instance {instance_id}")

        # TODO: format and mount attached EBS
        ssh.run(instance_dns, cmd="sudo mkdir /mnt/ebs_export/", verbose=True)
        ssh.run(instance_dns, cmd="sudo mkfs -t ext4 /dev/xvdf", verbose=True)
        ssh.run(instance_dns, cmd="sudo mount -t ext4 /dev/xvdf /mnt/ebs_export/", verbose=True)
        ssh.run(instance_dns, cmd="sudo mkdir /mnt/ebs_export/ethereum", verbose=True)
        ssh.run(instance_dns, cmd="sudo chown ec2-user:ec2-user /mnt/ebs_export/ethereum", verbose=True)

        # TODO: sanity check free space on ebs_export copy datadir

        # TODO: copy data
        ssh.run(instance_dns, cmd="cp --recursive /mnt/ebs/ethereum/* /mnt/ebs_export/ethereum/", verbose=True)

        # TODO: verify datadir

        # TODO: umount and then aws detach ebs
        ssh.run(instance_dns, cmd="sudo umount /mnt/ebs_export", verbose=True)

        # TODO: terminate initial sync server
        ec2.terminate_ec2_instance(ec2_client, instance_id)

        return True
    else:
        logger.info("Finished with errors")
        return False


def _wait_for_sync_completion(instance_dns, instance_type, datadir_mount, data_dir, interrupt_avail_pct=3.0, status_interval_secs=15):
    logger.info(f"Monitoring geth synchronisation. This should take several hours to complete...")

    status_count = 0
    max_perc_block = -1
    while True:
        status_count += 1
        status, avail_pct, detail, perc_block = geth_status.status(instance_dns, datadir_mount, data_dir)
        if perc_block > max_perc_block:
            max_perc_block = perc_block
        logger.info(f"\nGETH STATUS #{status_count} ({instance_type}, {avail_pct:.2f}% disk available, {max_perc_block:.2f}% blocks):\n"
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

    return status, instance_type, avail_pct, detail, max_perc_block


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
    logger.warning(f"geth version '{version}'")
    expected_version = "1.10.9-stable"
    if version != expected_version:
        logger.warning(f"App tested with geth '{expected_version}' and your server is running '{version}'")

    status, instance_type, avail_pct, detail, perc_block = \
        _wait_for_sync_completion(instance_dns, instance_type, datadir_mount, data_dir)

    success = \
        _process_completed_sync(instance_dns, status, ec2_client, data_dir, az_name, instance_id, instance_type, version, perc_block)

    # TODO: start smaller instance, attach ebs and kick off ongoing sync server

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
