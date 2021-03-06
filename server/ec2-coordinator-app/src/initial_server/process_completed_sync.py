import math
from datetime import datetime
from loguru import logger
from library import ebs, ec2, ssh, geth_status


def process(instance_dns, app_ver, status, ec2_client, data_dir, az_name, instance_id, instance_type,
            version, debug_run, force_save_to_ebs, terminate_instance, ebs_factor):
    logger.info(f"Started process completed sync. Status '{status}'")

    if debug_run or force_save_to_ebs or status == geth_status.GethStatusEnum.stopped_success:
        datadir_size_mb = ssh.geth_du(instance_dns, data_dir)
        assert datadir_size_mb > 0

        uptime_pretty = ssh.uptime_pretty(instance_dns)
        (current_block, highest_block, perc_block) = ssh.get_block_info(instance_dns)

        geth_cmd = ssh.get_geth_cmd(instance_dns)

        datadir_gb = datadir_size_mb/1.024e+6  # TODO: GiB vs GB
        logger.info(f"Size of datadir is {datadir_gb:.2f}GB")

        ebs_size_gb = int(math.ceil(datadir_gb * ebs_factor / 10.0)) * 10  # Round up nearest 10GB
        logger.info(f"Calc size of new EBS is {ebs_size_gb:.2f}GB (x{ebs_factor:.2f} rounded up to nearest 10GB)")
        logger.warning(f"Estimated cost for {ebs_size_gb:.2f}GB EBS is ${(ebs_size_gb*0.1):.2f} USD/month "
                       f"(assuming us-east-1, gp2, no snapshot, {ebs_size_gb:.2f}GB * $0.10 USD)")

        # TODO: review device
        # TODO: check if created already by tag

        ebs_device = "/dev/xvdf"  # TODO: review by instance type
        ebs_tags = [
            {"Key": "Name", "Value": "ethereum-initial-sync-server-ebs-export"},
            {"Key": "deployment", "Value": "boto"},
            {"Key": "app_name", "Value": "cloud-ethereum-node"},
            {"Key": "env", "Value": "prd"},
            {"Key": "meta_app_ver", "Value": app_ver},
            {"Key": "meta_sync_date", "Value": datetime.now().replace(microsecond=0).isoformat()},
            {"Key": "meta_ec2_uptime", "Value": uptime_pretty},
            {"Key": "meta_ec2_instance_id", "Value": instance_id},
            {"Key": "meta_ec2_instance_type", "Value": instance_type},
            {"Key": "meta_geth_status", "Value": status.name},
            {"Key": "meta_geth_current_block", "Value": current_block},
            {"Key": "meta_geth_highest_block", "Value": highest_block},
            {"Key": "meta_geth_perc_block", "Value": perc_block},
            {"Key": "meta_geth_version", "Value": version},
            {"Key": "meta_geth_cmd", "Value": geth_cmd},
            {"Key": "meta_ebs_device", "Value": ebs_device},
            {"Key": "meta_ebs_data_dir", "Value": data_dir},
            {"Key": "meta_ebs_datadir_gb", "Value": "{:.2f}".format(datadir_gb)},
            {"Key": "meta_ebs_size_gb", "Value": "{:.2f}".format(ebs_size_gb)},
            {"Key": "meta_config_debug_run", "Value": str(debug_run)},
            {"Key": "meta_config_force_save_to_ebs", "Value": str(force_save_to_ebs)},
            {"Key": "meta_config_terminate_instance", "Value": str(terminate_instance)},
        ]

        logger.info(f"Create and attach {ebs_size_gb:.2f}GB EBS volume to instance {instance_id} with volume Tags: {ebs_tags}")
        ebs_success, volume_id = ebs.create_and_attach_volume(
            ec2_client, az_name, instance_id, device=ebs_device, size_gb=ebs_size_gb, tags=ebs_tags)
        if not ebs_success:
            raise RuntimeError(f"Failed to create and attach volume to instance {instance_id}")

        format_cmds = [
            "sudo mkdir /mnt/ebs_export/",
            "sudo mkfs -t ext4 /dev/xvdf",
            "sudo mount -t ext4 /dev/xvdf /mnt/ebs_export/",
            "sudo mkdir /mnt/ebs_export/ethereum",
            "sudo chown ec2-user:ec2-user /mnt/ebs_export/ethereum",
            "sudo mkdir /mnt/ebs_export/initial_sync_metadata",
            "sudo chown ec2-user:ec2-user /mnt/ebs_export/initial_sync_metadata",
        ]
        ssh.run_many(instance_dns, "Format and mount attached EBS", format_cmds, verbose=True)

        # TODO: sanity check free space on ebs_export copy datadir

        # TODO: copy data to ebs_export
        format_cmds = [
            "cp --recursive /mnt/sync/ethereum/* /mnt/ebs_export/ethereum/",
            "cp /home/ec2-user/user_data.log /mnt/ebs_export/initial_sync_metadata/user_data.log",
            "cp /home/ec2-user/geth_cmd.txt /mnt/ebs_export/initial_sync_metadata/geth_cmd.txt",
            "head -n 1000 /home/ec2-user/geth_nohup.out >> /mnt/ebs_export/initial_sync_metadata/head_geth_nohup.out",
            "tail -n 1000 /home/ec2-user/geth_nohup.out >> /mnt/ebs_export/initial_sync_metadata/tail_geth_nohup.out",
        ]
        ssh.run_many(instance_dns, "Copy chaindata and metadata to attached EBS", format_cmds, verbose=True)

        # TODO: verify datadir

        # TODO: umount and then aws detach ebs
        ssh.run(instance_dns, cmd="sudo umount /mnt/ebs_export", verbose=True)

        # TODO: terminate initial sync server
        if terminate_instance:
            ec2.terminate_ec2_instance(ec2_client, instance_id)
        else:
            logger.warning(f"Skipping termination of {instance_type} instance {instance_id}")

        return True
    else:
        logger.info("Finished with errors")
        logger.warning(f"Skipping termination of {instance_type} instance {instance_id}")
        return False
