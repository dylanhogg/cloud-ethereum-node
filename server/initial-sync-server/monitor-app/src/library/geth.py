from enum import Enum
from loguru import logger
from library import ssh


class GethStatus(Enum):
    unknown = 1
    not_started = 2
    running = 3
    running_error = 4
    stopped_success = 5
    stopped_interrupt = 6
    stopped_error = 7


def status(instance_dns):
    detail = []

    error = False
    running = False
    interrupted = False
    complete = False
    empty = False

    pid = ssh.geth_pid(instance_dns)
    if pid is None:
        detail.append("geth stopped (no pid)")
    else:
        detail.append(f"geth running (pid {pid})")
        running = True

    # TODO: datadir usage GiB
    # TODO: disk free
    # TODO: disk names
    # TODO: disk lsblk

    # Disk usage
    usage_mb = ssh.geth_du(instance_dns)
    if usage_mb == 0:
        empty = True
    detail.append(f"geth disk usage is {usage_mb/1.024e+6}GiB / {usage_mb/1.0e+6}GB")

    # Log file
    logs = ssh.geth_logs(instance_dns, 50).lower()
    log_lines = logs.strip().split("\n")

    # Bad/incomplete log lines
    if "crit [" in logs:
        detail.append("*** Critical occurred ***")
        error = True
    if "error [" in logs:
        detail.append("*** Error occurred ***")
        error = True  # TODO: review case, may not be serious
    if "no space left on device" in logs:
        detail.append("No space left on device")
        error = True
    if "got interrupt, shutting down" in logs:
        detail.append("Got interrupt, shutting down")
        interrupted = True

    # In progress info log lines
    if "block synchronisation started" in logs:
        detail.append("Block synchronisation started")
    if "imported new block receipts" in logs:
        detail.append("Imported new block receipts")
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
    geth_status = GethStatus.unknown

    if running and not error:
        geth_status = GethStatus.running
    if running and error:
        geth_status = GethStatus.running_error
    elif not running and empty:
        geth_status = GethStatus.not_started
    elif not running and error:
        geth_status = GethStatus.stopped_error
    elif not running and interrupted:
        geth_status = GethStatus.stopped_interrupt
    elif not running and complete:
        geth_status = GethStatus.stopped_success

    return geth_status, detail
