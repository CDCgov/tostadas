# !/bin/bash

# Update the System
sudo apt-get update
sudo apt upgrade -y

# Install Necessary Packages 
sudo apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev squashfs-tools libseccomp-dev wget pkg-config git cryptsetup

# Check system architecture
ARCH=$(uname -m)
case $ARCH in
  x86_64)
    GO_TARBALL="go1.17.linux-amd64.tar.gz"
    ;;
  aarch64 | arm64 | armv8l)
    GO_TARBALL="go1.17.linux-arm64.tar.gz"
    ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

# Install Go
wget https://golang.org/dl/$GO_TARBALL
sudo tar -C /usr/local -xzf $GO_TARBALL
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# Install Singularity
export VERSION=3.8.3
wget https://github.com/hpcng/singularity/releases/download/v${VERSION}/singularity-${VERSION}.tar.gz
tar -xzf singularity-${VERSION}.tar.gz
cd singularity-${VERSION}
./mconfig
make -C builddir
sudo make -C builddir install