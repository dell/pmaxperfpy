#!/bin/bash
basedir=$(pwd)
port=8080

docker run \
	--publish $port:8080 \
	--detach=true \
	--network="host" \
	--volume $basedir/pmaxperf.cfg:/pmaxperfpy/pmaxperf.cfg \
	--name pmaxperfpy \
	pmaxperfpy:latest
