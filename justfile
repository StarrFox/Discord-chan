#!/usr/bin/env just --justfile

build:
    docker build --tag starrfox_bot .

run:
    docker-compose up --build -d
