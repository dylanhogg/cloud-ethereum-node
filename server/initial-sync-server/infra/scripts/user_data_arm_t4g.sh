#!/bin/bash

# arm64 / t4g.medium
echo "user_data started on arm64" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log

# Download arm64 geth
wget https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.10.9-eae3b194.tar.gz
tar -xzf geth-linux-arm64-1.10.9-eae3b194.tar.gz
mv geth-linux-arm64-1.10.9-eae3b194/geth /home/ec2-user/geth
chown ec2-user:ec2-user /home/ec2-user/geth

# Mount disks - not requied

 # Create datadir
mkdir /home/ec2-user/ethereum
chown ec2-user:ec2-user /home/ec2-user/ethereum

# Run geth on arm64 / t4g.medium
nohup sudo -u ec2-user /home/ec2-user/geth --datadir /home/ec2-user/ethereum --nousb --syncmode snap --exitwhensynced &> /home/ec2-user/geth_nohup.out &

# BLOG: ./geth --datadir /mnt/nvm/ether --syncmode=fast --maxpeers=100 --cache=28000

# I3  : ./geth --datadir /mnt/nvm/ether --syncmode snap --maxpeers 100 --cache 28000 --gcmode archive --exitwhensynced
#       ^^^ syncmode snap; --gcmode archive; --exitwhensynced to finish safely; formatting with spaces

# TG4 : ./geth ... --nousb
#        ^^^ requires nousb to remove warnings

echo "user_data completed" >> /home/ec2-user/user_data.log
echo `date` >> /home/ec2-user/user_data.log
chown ec2-user:ec2-user /home/ec2-user/user_data.log