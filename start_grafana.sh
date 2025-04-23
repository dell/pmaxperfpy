#!/bin/bash
#basedir=$(pwd)
#cfgfile=$basedir/grafana.ini
#datavol=$basedir/datavol
#userid=472:1
#--user $userid \
#--volume $cfgfile:/etc/grafana/grafana.ini \
#--volume $datavol:/var/lib/grafana \
port=3000

docker run \
	--publish $port:3000 \
	--detach=true \
	--name grafana \
	grafana/grafana
