#!/bin/bash
port=8080

docker run \
	--publish $port:8080 \
	--detach=true \
	--mount type=bind,source=./pmax_config.json,target=/pmaxperfpy/pmax_config.json,readonly \
	--name pmaxperfpy \
	pmaxperfpy:latest
