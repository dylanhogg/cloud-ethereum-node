# amd64 / i3.xlarge
# wget https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.10.9-eae3b194.tar.gz
# tar -xzf geth-linux-amd64-1.10.9-eae3b194.tar.gz
# mv geth-linux-amd64-1.10.9-eae3b194/geth ~/

# arm64 / t4g.medium
wget https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.10.9-eae3b194.tar.gz
tar -xzf geth-linux-arm64-1.10.9-eae3b194.tar.gz
mv geth-linux-arm64-1.10.9-eae3b194/geth ~/

# t4g.medium (TODO)
~/geth --syncmode snap --nousb

# i3.xlarge (REVIEW)
# ./geth --datadir /mnt/nvm/ether --syncmode snap --maxpeers 100 --cache 28000 --gcmode archive
