#!/bin/bash

# Function to check CUDA version
check_cuda_version() {
  if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep -oP 'release \K[0-9]+\.[0-9]+')
    if [[ "$CUDA_VERSION" == "12.1" ]]; then
      echo "CUDA 12.1 is already installed."
      return 0
    else
      echo "CUDA version $CUDA_VERSION is installed. Expected version is 12.1."
      return 1
    fi
  else
    echo "CUDA is not installed."
    return 1
  fi
}

# Function to install CUDA 12.1
add_install_cuda() {
  echo "Installing CUDA 12.1..."
  sudo apt update && sudo apt upgrade -y
  sudo ubuntu-drivers autoinstall
  wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
  sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
  wget https://developer.download.nvidia.com/compute/cuda/12.1.1/local_installers/cuda-repo-ubuntu2204-12-1-local_12.1.1-530.30.02-1_amd64.deb
  sudo dpkg -i cuda-repo-ubuntu2204-12-1-local_12.1.1-530.30.02-1_amd64.deb
  sudo cp /var/cuda-repo-ubuntu2204-12-1-local/cuda-*-keyring.gpg /usr/share/keyrings/
  sudo apt-get update
  sudo apt-get -y install cuda-12-1
  echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
}

# Function to check GPU availability
check_gpu() {
  if ! nvidia-smi &> /dev/null; then
    echo "GPUs are not accessible."
    return 1
  else
    echo "GPUs are accessible."
    return 0
  fi
}

# Function to check if NVIDIA container toolkit is installed
check_nvidia_container_toolkit() {
  if ! docker info | grep -i runtime | grep -q nvidia && ! nvidia-container-cli --version &> /dev/null; then
    echo "NVIDIA container toolkit is not installed."
    return 1
  else
    echo "NVIDIA container toolkit is already installed."
    return 0
  fi
}

# Function to install NVIDIA container toolkit
install_nvidia_container_toolkit() {
  echo "Installing NVIDIA container toolkit..."
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  # TODO: check the below command
  sudo sed -i -e '/experimental/ s/^//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
}

# Main script logic
if ! check_cuda_version; then
  read -p "Do you want to install CUDA 12.1? (y/n): " install_cuda_choice
  if [[ "$install_cuda_choice" == "y" ]]; then
    add_install_cuda
    read -p "Do you want to reboot the system now? (y/n): " reboot_choice
    if [[ "$reboot_choice" == "y" ]]; then
      sudo reboot
    else
      echo "Please reboot the system manually for changes to take effect."
    fi
  else
    echo "CUDA 12.1 installation skipped."
  fi
else
  if ! check_gpu; then
    read -p "GPUs are not accessible. Do you want to reboot the system now? (y/n): " reboot_choice
    if [[ "$reboot_choice" == "y" ]]; then
      sudo reboot
    else
      echo "Please reboot the system manually to check GPU accessibility."
    fi
  fi
fi

if ! check_nvidia_container_toolkit; then
  read -p "Do you want to install NVIDIA container toolkit? (y/n): " install_toolkit_choice
  if [[ "$install_toolkit_choice" == "y" ]]; then
    install_nvidia_container_toolkit
  else
    echo "NVIDIA container toolkit installation skipped."
  fi
fi
