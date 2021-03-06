#!/bin/bash

# arm64 / t4g.medium

DATA_DIR="/mnt/sync/ethereum"

echo "user_data started on arm64" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
echo "datadir: $DATA_DIR" >> /home/ec2-user/user_data.log

yum -y update

# Download arm64 geth
wget https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.10.15-8be800ff.tar.gz
tar -xzf geth-linux-arm64-1.10.15-8be800ff.tar.gz
mv geth-linux-arm64-1.10.15-8be800ff/geth /home/ec2-user/geth
chown ec2-user:ec2-user /home/ec2-user/geth

# Mount disks - not requied on t4g




# Create datadir
mkdir -p $DATA_DIR
chown ec2-user:ec2-user $DATA_DIR

# TODO: get geth running...

# Run geth on arm64 / t4g.medium
# nohup sudo -u ec2-user /home/ec2-user/geth --datadir $DATA_DIR --nousb --syncmode snap --exitwhensynced &> /home/ec2-user/geth_nohup.out &
# chown ec2-user:ec2-user /home/ec2-user/geth_nohup.out
# nohup /home/ec2-user/geth --datadir /mnt/sync/ethereum --nousb --syncmode snap --exitwhensynced &> /home/ec2-user/geth_nohup.out &

# BLOG: ./geth --datadir /mnt/nvm/ether --syncmode=fast --maxpeers=100 --cache=28000

# I3  : ./geth --datadir /mnt/nvm/ether --syncmode snap --maxpeers 100 --cache 28000 --gcmode archive --exitwhensynced
#       ^^^ syncmode snap; --gcmode archive; --exitwhensynced to finish safely; formatting with spaces

# TG4 : ./geth ... --nousb
#        ^^^ requires nousb to remove warnings

echo "user_data completed" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
chown ec2-user:ec2-user /home/ec2-user/user_data.log
