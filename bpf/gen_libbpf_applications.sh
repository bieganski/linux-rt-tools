#!/bin/bash

set -eu


# Check if an argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <ARCH (riscv64|armv7l)>"
    exit 1
fi

# Assign the argument to ARCH variable
ARCH="$1"

# Check the value of ARCH
if [ "$ARCH" != "riscv64" ] && [ "$ARCH" != "armv7l" ]; then
    echo "Invalid ARCH value. Allowed values are riscv64 and armv7l."
    exit 1
fi


OUT_DIR=libbpf.applications.$ARCH

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

if [ "$ARCH" == "riscv64" ]; then
COMPILER=gcc-riscv64-linux-gnu
else
COMPILER=gcc-arm-linux-gnueabi
fi

cat <<EOF > Dockerfile
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install -y build-essential pkg-config git
RUN apt-get install -y libelf-dev $COMPILER llvm clang
RUN ln -s /usr/include/asm-generic /usr/include/asm
RUN git clone -b mateusz-armv7l --recurse-submodules https://github.com/bieganski/bcc.git bcc
WORKDIR /bcc/libbpf-tools
RUN ./build.sh $ARCH
EOF


docker build . -t libbpf-$ARCH

mkdir -p $OUT_DIR
id=$(docker create libbpf-$ARCH)
docker cp $id:/bcc/libbpf-tools/ .
docker rm -v $id

chmod a+rw libbpf-tools/*

find libbpf-tools/ -type f  | xargs file | grep ELF | grep executable | cut -d : -f 1 | xargs -I{} cp {} $OUT_DIR

