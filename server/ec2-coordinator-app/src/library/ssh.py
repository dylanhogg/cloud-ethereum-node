import re
import time
import subprocess
from loguru import logger


# TODO: make this module a class and set these in ctr
geth_executable = "/home/ec2-user/geth"
default_ssh_key = "../initial-sync-server/keys/id_rsa"


def run_many(instance_dns, description, cmds, verbose=False):
    if description is not None:
        logger.info("Start: " + description)

    for cmd in cmds:
        run(instance_dns, cmd, verbose=verbose)

    if description is not None:
        logger.info("Complete: " + description)


def run(instance_dns, cmd, user="ec2-user", key=None, verbose=False):
    # TODO: consider using https://github.com/paramiko/paramiko
    if key is None:
        key = default_ssh_key

    if verbose:
        logger.info(f"ssh cmd: {cmd}")

    ssh_cmd = f'ssh -o "StrictHostKeyChecking no" -i "{key}" {user}@{instance_dns} "{cmd}"'
    out, err = subprocess.Popen(ssh_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    # Connection refused could be because the instance isn't ready yet
    if "connection refused" in err.decode().lower():
        logger.warning(f"Connection refused for ssh cmd: '{cmd}': {err.decode()}")
        logger.info(f"Pausing before retrying ssh cmd: '{cmd}'")
        time.sleep(60)
        out, err = subprocess.Popen(ssh_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if "connection refused" in err.decode().lower():
            raise RuntimeError(f"Connection refused (again) for ssh cmd: '{cmd}': {err.decode()}")

    # Timed out is likely security group/firewall issue
    if "timed out" in err.decode().lower():
        raise RuntimeError(f"ssh timed out, check instance_dns and port 22 ingress allowed: {err.decode()}")

    # Not all errors are critical, so just log them
    if len(err.decode()) > 0:
        logger.warning(err.decode().lower())

    result = out.decode().strip()
    if verbose and len(result) > 0:
        logger.info(f"ssh cmd '{cmd}' result: {result}")
    return result


def _rpc(instance_dns, data_dir, ethjs):
    # TODO: Consider calling rcp server http.port 8545 directly
    #       Needs geth to startup with different options and open firewall port
    cmd = f"{geth_executable} attach ipc:{data_dir}/geth.ipc --exec '{ethjs}'"
    return run(instance_dns, cmd)


def geth_version(instance_dns):
    # This is a good method to verify geth is installed and the instance is ready
    cmd = f"{geth_executable} version"
    response = run(instance_dns, cmd)
    if len(response) == 0:
        logger.warning(f"geth_version returned empty, pause before retry...")
        time.sleep(60)
        response = run(instance_dns, cmd)
        if len(response) == 0:
            raise RuntimeError(f"geth_version returned empty again")
    matches = [x for x in response.split("\n") if "version" in x.lower()]
    if len(matches) == 0:
        raise RuntimeError(f"Couldn't find verion information from 'geth version': {response}")
    return matches[0].lower().replace("version:", "").strip()


def ps(instance_dns, all_users=False):
    cmd = "ps -aux" if all_users else "ps -ux"
    return run(instance_dns, cmd)


def geth_pid(instance_dns):
    procs = run(instance_dns, "ps -e -o pid,cmd | grep geth")
    lines = procs.strip().split("\n")

    # Match `--datadir` to skip grep command, and exclude `sudo` to skip parent process
    matches = [x for x in lines if "--datadir" in x and "sudo" not in x]
    assert len(matches) <= 1
    if len(matches) == 0:
        return None

    return int(matches[0].strip().split(" ")[0])


def geth_logs(instance_dns, n, logfile="/home/ec2-user/geth_nohup.out"):
    return run(instance_dns, f"tail -n{n} {logfile}")


def userdata_logs(instance_dns, n, logfile="/var/log/cloud-init-output.log"):
    return run(instance_dns, f"tail -n{n} {logfile}")


def du(instance_dns, human=False):
    cmd = "du -h" if human else "du"
    return run(instance_dns, cmd)


def geth_du(instance_dns, data_dir):
    usage = run(instance_dns, f"du -s {data_dir}")
    assert len(usage.split("\t")) == 2
    return int(usage.split("\t")[0])


def df(instance_dns, human=False):
    cmd = "df -h" if human else "df"
    return run(instance_dns, cmd)


def df_mount(instance_dns, datadir_mount):
    all_df = run(instance_dns, "df")
    lines = all_df.strip().split("\n")

    matches = [x for x in lines if x.endswith(datadir_mount)]
    if len(matches) != 1:
        error = f"Expected 1 match for df on datadir_mount {datadir_mount}, but got {len(matches)}: {matches}"
        logger.error(error)
        raise RuntimeError(error)

    match = matches[0]
    match_tabbed = "\t".join(match.split())  # Replace spaces with a tab

    # Grap columns from: [Filesystem, 1K-blocks, Used, Available, Use%, Mounted on]
    used_kb = int(match_tabbed.split("\t")[2])
    avail_kb = int(match_tabbed.split("\t")[3])
    avail_pct = (avail_kb*100)/(used_kb+avail_kb)
    return used_kb, avail_kb, avail_pct


def lsblk(instance_dns):
    return run(instance_dns, "lsblk")


def uptime(instance_dns):
    return run(instance_dns, "uptime")


def geth_sigint(instance_dns):
    pid = geth_pid(instance_dns)
    if pid is None:
        logger.warning("Cannot kill geth process since it is not running")
    run(instance_dns, f"kill -SIGINT {pid}")
    return pid


# TODO: make wrapper from geth.py
def rpc_syncing(instance_dns, data_dir):
    ethjs = "eth.syncing"
    response = _rpc(instance_dns, data_dir, ethjs)

    if response == "false":
        return False, None, None,

    try:
        current_block = -1
        highest_block = -1
        # NOTE: Unfortunately the response can't be parsed by json.loads :(
        for line in response.lower().split("\n"):
            if "currentblock" in line:
                current_block = int(re.findall(r"\d+", line)[0])
            if "highestblock" in line:
                highest_block = int(re.findall(r"\d+", line)[0])
        return True, current_block, highest_block
    except Exception as ex:
        logger.error(f"Could not parse geth rpc response: {response} due to {ex}")
        return False, None, None



