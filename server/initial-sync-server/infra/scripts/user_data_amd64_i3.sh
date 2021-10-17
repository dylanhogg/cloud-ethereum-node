#!/bin/bash

# amd64 / i3.xlarge
echo "user_data started on amd64" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log

# Download amd64 geth
wget https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.10.9-eae3b194.tar.gz
tar -xzf geth-linux-amd64-1.10.9-eae3b194.tar.gz
mv geth-linux-amd64-1.10.9-eae3b194/geth /home/ec2-user/geth
chown ec2-user:ec2-user /home/ec2-user/geth

# Mount disks
mkdir /mnt/nvm/
mkfs -t ext4 /dev/nvme0n1
mount -t ext4 /dev/nvme0n1 /mnt/nvm

# Create datadir
mkdir /mnt/nvm/ethereum
chown ec2-user:ec2-user /mnt/nvm/ethereum

# Run geth on amd64 / i3.xlarge
# TODO: review --gcmode archive
nohup sudo -u ec2-user /home/ec2-user/geth --datadir /mnt/nvm/ethereum --nousb --syncmode snap --maxpeers 100 --cache 28000 --exitwhensynced &> /home/ec2-user/geth_nohup.out &

# BLOG: ./geth --datadir /mnt/nvm/ether --syncmode=fast --maxpeers=100 --cache=28000

# I3  : ./geth --datadir /mnt/nvm/ether --syncmode snap --maxpeers 100 --cache 28000 --gcmode archive --exitwhensynced
#       ^^^ syncmode snap; --gcmode archive; --exitwhensynced to finish safely; formatting with spaces

# TG4 : ./geth ... --nousb
#        ^^^ requires nousb to remove warnings

echo "user_data completed" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
chown ec2-user:ec2-user /home/ec2-user/user_data.log
