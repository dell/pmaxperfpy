#!/bin/bash
basedir=$(pwd)
cfgfile=$basedir/prometheus_config.yml
port=9090
#datavol=$basedir/datavol
#userid=486:486
#--user $userid \
#--volume $datavol:/prometheus \

docker run \
	--publish $port:9090 \
	--detach=true \
	--volume $cfgfile:/etc/prometheus/prometheus.yml \
	--name prometheus \
	prom/prometheus
