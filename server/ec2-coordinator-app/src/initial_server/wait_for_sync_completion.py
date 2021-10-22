import time
from loguru import logger
from library import ssh, geth_status


def wait(instance_dns, instance_type, datadir_mount, data_dir,
         debug_run, interrupt_avail_pct=3.0, status_interval_secs=15):
    logger.info(f"Monitoring geth synchronisation. This should take several hours to complete...")

    status_count = 0
    max_perc_block = -1
    while True:
        if debug_run:
            logger.warning(f"debug_run set to True; will interrupt sync prematurely!")

        status_count += 1
        status, avail_pct, detail, perc_block = geth_status.status(instance_dns, datadir_mount, data_dir)
        if perc_block > max_perc_block:
            max_perc_block = perc_block
        logger.info(f"\nGETH STATUS #{status_count} ({instance_type}, {avail_pct:.2f}% disk available, {max_perc_block:.2f}% blocks):\n"
                    + "\n".join(detail))

        if status.name.startswith("stopped"):
            logger.info(f"Exiting monitoring due to geth status {status}")
            break

        if avail_pct < interrupt_avail_pct:
            # TODO: review
            pid = ssh.geth_sigint(instance_dns)
            logger.info("Disk free:\n" + ssh.df(instance_dns, human=True))
            logger.info("Disk usage:\n" + ssh.du(instance_dns, human=True))
            logger.error(f"Interrupting geth process {pid} due to only {avail_pct:.2f}% avaiable on volume")
            break

        if debug_run and perc_block > 5.0:
            logger.warning(f"Prematurely interrupt geth process in debug case for testing (perc_block {perc_block:.2f}%)")
            ssh.geth_sigint(instance_dns)

        time.sleep(status_interval_secs)

    return status, instance_type, avail_pct, detail, max_perc_block
