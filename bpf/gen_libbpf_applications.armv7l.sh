#!/bin/bash

set -eu

OUT_DIR=libbpf.applications.armv7l

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

cat <<EOF > Dockerfile
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install -y build-essential pkg-config git
RUN apt-get install -y libelf-dev gcc-arm-linux-gnueabi llvm clang
RUN ln -s /usr/include/asm-generic /usr/include/asm
RUN git clone -b mateusz-armv7l --recurse-submodules https://github.com/bieganski/bcc.git bcc
WORKDIR /bcc/libbpf-tools
RUN ./build.sh
EOF


docker build . -t libbpf-armv7l

mkdir -p $OUT_DIR
id=$(docker create libbpf-armv7l)
docker cp $id:/bcc/libbpf-tools/ .
docker rm -v $id

chmod a+rw libbpf-tools/*

find libbpf-tools/ -type f  | xargs file | grep ELF | grep executable | cut -d : -f 1 | xargs -I{} cp {} $OUT_DIR

