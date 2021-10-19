import subprocess
from loguru import logger


def _run(instance_dns, cmd, user="ec2-user", key="../keys/id_rsa"):
    # TODO: consider https://stackoverflow.com/questions/3586106/perform-commands-over-ssh-with-python
    ssh_cmd = f'ssh -o "StrictHostKeyChecking no" -i "{key}" {user}@{instance_dns} "{cmd}"'
    p = subprocess.Popen(ssh_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    assert len(p) > 0, "Unexpected result length from subprocess.Popen"
    return p[0].decode().strip()


def ps(instance_dns, all_users=False):
    cmd = "ps -aux" if all_users else "ps -ux"
    return _run(instance_dns, cmd)


def geth_logs(instance_dns, n=20, logfile="/home/ec2-user/geth_nohup.out"):
    return _run(instance_dns, f"tail -n{n} {logfile}")


def userdata_logs(instance_dns, n=20, logfile="/var/log/cloud-init-output.log"):
    return _run(instance_dns, f"tail -n{n} {logfile}")


def geth_du(instance_dns, geth_dir="/mnt/ebs/ethereum"):
    du = _run(instance_dns, f"du -s {geth_dir}")
    assert len(du.split("\t")) == 2
    return int(du.split("\t")[0])


def geth_pid(instance_dns):
    procs = _run(instance_dns, "ps -e -o pid,cmd | grep geth")
    lines = procs.strip().split("\n")

    # Match `--datadir` to skip grep command, and exclude `sudo` to skip parent process
    matches = [x for x in lines if "--datadir" in x and "sudo" not in x]
    assert len(matches) <= 1
    if len(matches) == 0:
        return None

    return int(matches[0].strip().split(" ")[0])


def df(instance_dns):
    return _run(instance_dns, "df")


def lsblk(instance_dns):
    return _run(instance_dns, "lsblk")



