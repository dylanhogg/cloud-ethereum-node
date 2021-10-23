#!/bin/bash

# arm64 / t4g.medium

DATA_DIR="/mnt/sync/ethereum"
GETH_VER="geth-linux-arm64-1.10.9-eae3b194"
GETH_CMD="/home/ec2-user/geth --datadir $DATA_DIR --nousb --syncmode snap --exitwhensynced"

echo "user_data started on arm64" >> /home/ec2-user/user_data.log
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

# Mount disks - not requied on t4g




# Create datadir
mkdir -p $DATA_DIR
chown ec2-user:ec2-user $DATA_DIR

# Run geth
nohup sudo -u ec2-user $GETH_CMD &> /home/ec2-user/geth_nohup.out &
chown ec2-user:ec2-user /home/ec2-user/geth_nohup.out

echo "user_data completed" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
chown ec2-user:ec2-user /home/ec2-user/user_data.log
