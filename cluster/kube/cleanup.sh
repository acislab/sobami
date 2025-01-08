#!/bin/bash
# check if kubelet is running
sudo systemctl status kubelet

# if not, check the logs
sudo journalctl -u kubelet

# make sure cri is not disabled in containerd.toml file
sudo vim /etc/containerd/config.toml

# restart containerd
sudo systemctl restart containerd

# make sure swap is turned off
sudo swapoff -a

# restart kubelet
sudo systemctl restart kubelet

# reset kubeadm
sudo kubeadm reset


# Sometimes the cluster creation fails with tls issues, I have found that restarting kubelet services fixes that issue. (Still need to figure out what actually goes wrong though!)