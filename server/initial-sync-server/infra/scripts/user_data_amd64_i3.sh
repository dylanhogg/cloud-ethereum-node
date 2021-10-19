#!/bin/bash

# amd64 / i3.xlarge

DATA_DIR="/mnt/ebs/ethereum"

echo "user_data started on amd64" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
echo $DATA_DIR >> /home/ec2-user/user_data.log

# Download amd64 geth
wget https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.10.9-eae3b194.tar.gz
tar -xzf geth-linux-amd64-1.10.9-eae3b194.tar.gz
mv geth-linux-amd64-1.10.9-eae3b194/geth /home/ec2-user/geth
chown ec2-user:ec2-user /home/ec2-user/geth

# Mount direct attached storage disks (​​i3 only)
mkdir /mnt/ebs/
mkfs -t ext4 /dev/nvme0n1
mount -t ext4 /dev/nvme0n1 /mnt/ebs

# Create datadir
mkdir -p $DATA_DIR
chown ec2-user:ec2-user $DATA_DIR

# Run geth on amd64 / i3.xlarge  (TODO: review --gcmode archive, --nousb)
nohup sudo -u ec2-user /home/ec2-user/geth --datadir $DATA_DIR --nousb --syncmode snap --maxpeers 100 --cache 28000 --exitwhensynced &> /home/ec2-user/geth_nohup.out &

# BLOG: ./geth --datadir /mnt/nvm/ether --syncmode=fast --maxpeers=100 --cache=28000

# I3  : ./geth --datadir /mnt/nvm/ether --syncmode snap --maxpeers 100 --cache 28000 --gcmode archive --exitwhensynced
#       ^^^ syncmode snap; --gcmode archive; --exitwhensynced to finish safely; formatting with spaces

# TG4 : ./geth ... --nousb
#        ^^^ requires nousb to remove warnings

echo "user_data completed" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
chown ec2-user:ec2-user /home/ec2-user/user_data.log
