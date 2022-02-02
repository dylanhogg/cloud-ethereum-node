#!/bin/bash

# amd64 / i3.xlarge

DATA_DIR="/mnt/sync/ethereum"
GETH_VER="geth-linux-amd64-1.10.15-8be800ff"
GETH_CMD="/home/ec2-user/geth --datadir $DATA_DIR --nousb --syncmode snap --maxpeers 100 --cache 28000 --exitwhensynced"

echo "user_data started on amd64" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
echo "DATA_DIR: $DATA_DIR" >> /home/ec2-user/user_data.log
echo "GETH_VER: $GETH_VER" >> /home/ec2-user/user_data.log
echo "GETH_CMD: $GETH_CMD" >> /home/ec2-user/user_data.log
echo $GETH_CMD >> /home/ec2-user/geth_cmd.txt

yum -y update

# Download geth
wget https://gethstore.blob.core.windows.net/builds/$GETH_VER.tar.gz
tar -xzf $GETH_VER.tar.gz
mv $GETH_VER/geth /home/ec2-user/geth
chown ec2-user:ec2-user /home/ec2-user/geth

# Mount direct attached storage disks (i3 only)
mkdir /mnt/sync/
mkfs -t ext4 /dev/nvme0n1
mount -t ext4 /dev/nvme0n1 /mnt/sync

# Create datadir
mkdir -p $DATA_DIR
chown ec2-user:ec2-user $DATA_DIR

# Run geth  (TODO: review --gcmode archive, --nousb)
nohup sudo -u ec2-user $GETH_CMD &> /home/ec2-user/geth_nohup.out &
chown ec2-user:ec2-user /home/ec2-user/geth_nohup.out

echo "user_data completed" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
chown ec2-user:ec2-user /home/ec2-user/user_data.log
