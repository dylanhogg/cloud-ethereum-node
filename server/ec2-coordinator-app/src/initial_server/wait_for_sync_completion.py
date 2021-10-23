import time
from loguru import logger
from library import ssh, geth_status


def wait(instance_dns, instance_type, datadir_mount, data_dir,
         debug_run, interrupt_avail_pct=3.0, status_interval_secs=15):
    logger.info(f"Monitoring geth synchronisation. This should take several hours to complete...")

    status_count = 0
    max_perc_block = -1
    max_current_block = -1
    max_highest_block = -1

    while True:
        if debug_run:
            logger.warning(f"debug_run set to True; will interrupt sync prematurely!")

        status_count += 1
        status, avail_pct, detail, perc_block, highest_block, current_block = \
            geth_status.status(instance_dns, datadir_mount, data_dir)

        if perc_block > max_perc_block:
            max_perc_block = perc_block
        if highest_block > max_highest_block:
            max_highest_block = highest_block
        if current_block > max_current_block:
            max_current_block = current_block
        logger.info(f"\nGETH STATUS #{status_count} ({instance_type}, {avail_pct:.2f}% disk available, "
                    f"{max_current_block:,} current, {max_highest_block:,} highest, {max_perc_block:.2f}% blocks):\n"
                    + "\n".join(detail))

        if max_current_block >= 0 and max_highest_block > 0:
            ssh.run(instance_dns, f"echo \"{max_current_block},{max_highest_block},{max_perc_block:.2f}%\""
                                  f" > /home/ec2-user/geth_block_info.txt")

        if status.name.startswith("stopped"):
            logger.info(f"Exiting monitoring due to geth status {status}")
            break

        if avail_pct < interrupt_avail_pct:
            # TODO: review the need to interrupt on low disk
            pid = ssh.geth_sigint(instance_dns)
            logger.info("Disk free:\n" + ssh.df(instance_dns, human=True))
            logger.info("Disk usage:\n" + ssh.du(instance_dns, human=True))
            logger.error(f"Interrupting geth process {pid} due to only {avail_pct:.2f}% avaiable on volume")
            break

        if debug_run and perc_block > 1.5:
            logger.warning(f"Prematurely interrupting geth process in debug case for testing (perc_block {perc_block:.2f}%)...")
            ssh.geth_sigint(instance_dns)

        time.sleep(status_interval_secs)

    return status, instance_type, avail_pct, detail, max_perc_block, max_highest_block, max_current_block
