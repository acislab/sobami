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
# reset kubeadm
sudo kubeadm reset
sudo rm -rf /etc/cni/net.d/*
sudo rm -rf /var/lib/kubelet/*
sudo rm -rf /etc/kubernetes/

# Sometimes the cluster creation fails with tls issues, I have found that restarting kubelet services fixes that issue. (Still need to figure out what actually goes wrong though!)

sudo systemctl stop kubelet
sudo systemctl disable kubelet

sudo apt-get purge -y kubeadm kubelet kubectl
sudo apt-get autoremove -y

sudo rm -rf /etc/kubernetes
sudo rm -rf ~/.kube
sudo rm -rf /var/lib/kubelet
sudo rm -rf /var/lib/etcd
sudo rm -rf /etc/systemd/system/kubelet.service.d
sudo rm -rf /usr/bin/kubeadm /usr/bin/kubectl /usr/bin/kubelet

sudo rm -rf /etc/cni/net.d
sudo rm -rf /var/lib/cni

sudo rm -rf /var/log/kubernetes
sudo rm -rf /var/run/kubernetes

kubeadm version
kubectl version
kubelet --version
