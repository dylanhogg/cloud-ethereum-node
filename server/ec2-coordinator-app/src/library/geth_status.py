from enum import Enum
from datetime import datetime
from loguru import logger
from library import ssh


class GethStatusEnum(Enum):
    unknown = 1
    not_started = 2
    running = 3
    running_error = 4
    stopped_success = 5
    stopped_interrupt = 6
    stopped_error = 7
    stopped_error_disk_full = 8


def status(instance_dns, datadir_mount, data_dir):
    logger.info("Collecting geth status...")

    error = False
    running = False
    interrupted = False
    complete = False
    empty_geth_dir = False
    disk_full = False
    perc_block = -1
    highest_block = -1
    current_block = -1

    detail = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        f"Instance DNS: {instance_dns}",
        f"Instance uptime: {ssh.uptime(instance_dns)}"
    ]

    # Process ID
    pid = ssh.geth_pid(instance_dns)
    if pid is None:
        detail.append("geth stopped (no pid)")
    else:
        running = True
        detail.append(f"geth running: pid {pid}")
        success, current_block, highest_block = ssh.rpc_syncing(instance_dns, data_dir)
        if success:
            diff_block = highest_block - current_block
            perc_block = (current_block*100/highest_block) if highest_block > 0 else -1
            detail.append(f"geth syncing: current {current_block:,}, highest {highest_block:,}, diff {diff_block:,}, {perc_block:.2f}%")
        else:
            detail.append(f"geth syncing: false")

    # Disk usage (TODO: work out GiB vs GB)
    usage_mb = ssh.geth_du(instance_dns, data_dir)
    if usage_mb == 0:
        empty_geth_dir = True
    detail.append(f"geth datadir usage ({data_dir}): {usage_mb/1.024e+6:.2f}GB")

    # Disk free (TODO: work out GiB vs GB)
    used_kb, avail_kb, avail_pct = ssh.df_mount(instance_dns, datadir_mount)
    detail.append(f"geth mount point ({datadir_mount}): "
                  f"Used={used_kb/1.024e+6:.2f}GB, Available={avail_kb/1.024e+6:.2f}GB / {avail_pct:.2f}%")
    if avail_pct < 1:
        detail.append(f"CRITICAL: Disk available percent is {avail_pct:.2f}%")
    elif avail_pct < 20:
        detail.append(f"WARNING: Disk available percent is {avail_pct:.2f}%")

    # Log file
    logs = ssh.geth_logs(instance_dns, 50).lower()
    log_lines = logs.strip().split("\n")

    # Bad/incomplete log lines
    if "crit [" in logs:
        detail.append("*** Critical occurred ***")
        error = True
    if "error [" in logs:
        detail.append("*** Error occurred ***")
        # error = True  # TODO: review case, may not be serious and shouldn't report error status?
    if "no space left on device" in logs:
        detail.append("No space left on device")
        error = True
        disk_full = True
    if "got interrupt, shutting down" in logs:
        detail.append("Got interrupt, shutting down")
        interrupted = True

    # In progress info log lines
    # if "block synchronisation started" in logs:
    #     detail.append("Block synchronisation started")
    # if "imported new block receipts" in logs:
    #     detail.append("Imported new block receipts")
    if "state sync in progress" in logs:
        detail.append("State sync in progress")
        matches = [x for x in log_lines if "state sync in progress" in x]
        detail.extend(matches[-1:])

    # Stopping info log lines
    if "ethereum protocol stopped" in logs:
        detail.append("Ethereum protocol stopped")
    if "transaction pool stopped" in logs:
        detail.append("Transaction pool stopped")
    if "http server stopped" in logs:
        detail.append("HTTP server stopped")
    if "ipc endpoint closed" in logs:
        detail.append("IPC endpoint closed")
    if "rewinding blockchain" in logs:
        detail.append("Rewinding blockchain")
    if "persisted the clean trie cache" in logs:
        detail.append("Persisted the clean trie cache")

    # Good log lines
    if "synchronisation completed" in logs:
        detail.append("Synchronisation completed")
        complete = True
    if "writing clean trie cache to disk" in logs:
        detail.append("Writing clean trie cache to disk")
    if "persisted the clean trie cache" in logs:
        detail.append("Persisted the clean trie cache")
    if "blockchain stopped" in logs:
        detail.append("Blockchain stopped")

    # Determine status, if possible (TODO: handle all cases here)
    geth_status = GethStatusEnum.unknown

    if running and not error:
        geth_status = GethStatusEnum.running
    if running and error:
        geth_status = GethStatusEnum.running_error
    elif not running and empty_geth_dir:
        geth_status = GethStatusEnum.not_started
    elif not running and disk_full:
        geth_status = GethStatusEnum.stopped_error_disk_full
    elif not running and error:
        geth_status = GethStatusEnum.stopped_error
    elif not running and interrupted:
        geth_status = GethStatusEnum.stopped_interrupt
    elif not running and complete:
        geth_status = GethStatusEnum.stopped_success

    detail.insert(1, geth_status.name)
    return geth_status, avail_pct, detail, perc_block, highest_block, current_block
