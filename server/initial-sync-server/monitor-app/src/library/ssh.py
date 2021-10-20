import re
import subprocess
from loguru import logger


geth_executable = "/home/ec2-user/geth"


def _run(instance_dns, cmd, user="ec2-user", key="../keys/id_rsa"):
    # TODO: consider https://stackoverflow.com/questions/3586106/perform-commands-over-ssh-with-python
    ssh_cmd = f'ssh -o "StrictHostKeyChecking no" -i "{key}" {user}@{instance_dns} "{cmd}"'
    out, err = subprocess.Popen(ssh_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    if "timed out" in err.decode().lower():
        raise RuntimeError(f"ssh timed out, check instance_dns and port 22 allowed from your IP: {err.decode()}")
    if len(err.decode()) > 0:
        logger.warning(err.decode())

    return out.decode().strip()


def _rpc(instance_dns, data_dir, ethjs):
    # TODO: call rcp server http.port 8545 directly - needs geth to startup with different options
    cmd = f"{geth_executable} attach ipc:{data_dir}/geth.ipc --exec '{ethjs}'"
    return _run(instance_dns, cmd)


def geth_version(instance_dns):
    cmd = f"{geth_executable} version"
    version_info = _run(instance_dns, cmd)
    matches = [x for x in version_info.split("\n") if "version" in x.lower()]
    if len(matches) == 0:
        raise RuntimeError(f"Couldn't find verion information from 'geth version': {version_info}")
    return matches[0].lower().replace("version:", "").strip()


def ps(instance_dns, all_users=False):
    cmd = "ps -aux" if all_users else "ps -ux"
    return _run(instance_dns, cmd)


def geth_pid(instance_dns):
    procs = _run(instance_dns, "ps -e -o pid,cmd | grep geth")
    lines = procs.strip().split("\n")

    # Match `--datadir` to skip grep command, and exclude `sudo` to skip parent process
    matches = [x for x in lines if "--datadir" in x and "sudo" not in x]
    assert len(matches) <= 1
    if len(matches) == 0:
        return None

    return int(matches[0].strip().split(" ")[0])


def geth_logs(instance_dns, n, logfile="/home/ec2-user/geth_nohup.out"):
    return _run(instance_dns, f"tail -n{n} {logfile}")


def userdata_logs(instance_dns, n, logfile="/var/log/cloud-init-output.log"):
    return _run(instance_dns, f"tail -n{n} {logfile}")


def du(instance_dns, human=False):
    cmd = "du -h" if human else "du"
    return _run(instance_dns, cmd)


def geth_du(instance_dns, data_dir):
    usage = _run(instance_dns, f"du -s {data_dir}")
    assert len(usage.split("\t")) == 2
    return int(usage.split("\t")[0])


def df(instance_dns, human=False):
    cmd = "df -h" if human else "df"
    return _run(instance_dns, cmd)


def df_mount(instance_dns, datadir_mount):
    all_df = _run(instance_dns, "df")
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
    return _run(instance_dns, "lsblk")


def uptime(instance_dns):
    return _run(instance_dns, "uptime")


def geth_sigint(instance_dns):
    pid = geth_pid(instance_dns)
    if pid is None:
        logger.warning("Cannot kill geth process since it is not running")
    _run(instance_dns, f"kill -SIGINT {pid}")
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



