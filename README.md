# PowerMax performance collector
Collect PowerMax performance data for use with Prometheus/Grafana or OpenTelemetry. PmaxPerfPy uses the PyU4V library to collect performance data from Unisphere, see https://github.com/dell/PyU4V.

![Grafana Dashboard](Grafana/dashboard_screenshot.png "Grafana Dashboard")

For customers interested in consuming **OpenTelemetry** data from the PowerMax performance collector, please see the OpenTelemetry section at the end of this README and the [OpenTelemetry README](OpenTelemetry/README.md)

## Installation
* Clone or copy the repository package to a local directory, for example /opt
```
cd /opt
git clone https://github.com/dell/pmaxperfpy
```

### Verify / edit requirements
The version of the PyU4V library has to match the Unisphere version of the PowerMax array. An older library version can still work but it is recommended to use the exact same version. By default, pmaxperfpy uses the latest available version. This can be changed in ```requirements.txt``` to the exact desired version, if needed.
```
$ cat requirements.txt
prometheus-client
pyu4v >= 10.1.0.2
```

### Add key and certificate (if required)
The collector uses plain HTTP, by default. If encryption (HTTPS/TLS) is required, please copy a key and certicate file to the app/ directory so they automatically will be included inside the container. And add the filenames without path to the defaults section in the config file.
The certificate should be in PEM format and can include chained intermediate / root CA certificate(s).
```
$ cat app/keyfile.key    # for your verification
$ cat app/certfile.cert  # for your verification
```
```json
"defaults": {
    "keyfile": "keyfile.key",
    "certfile": "certfile.cert"
}
```

### Build the container image
```
docker build -t pmaxperfpy:latest app
```

### Copy and edit the configuration file
* Please copy the provided pmax_config_example.json to pmax_config.json ``` cp pmax_config_example.json pmax_config.json ```

The config file uses JSON syntax. It has a defaults sections and then one or more unisphere sections. Parameters, like username and password, for example, can be specified at the defaults section (valid for all Unispheres) or can be overriden on a per Unisphere section.
Both username and password can be specfified as values directly or as a dictionary with the key "fromEnvironment" to take the value from an environment variable at runtime.

Example configuration file with three Unisphere instances. The first one uses username and password from the defaults section. The second Unisphere uses the same username but the password is provided by an environment variable at runtime. The third one uses the option powermax_serial to limit from which arrays metrics will be collected.
```json
"defaults": {
    "username": "smc",
    "password": "secret"
}
"unispheres": [
    {
        "hostname": "powermax1234.lab.local"
    },
    {
        "hostname": "5.6.7.8",
        "password": {
            "fromEnvironment": "PMAX5678_PASSWORD"
        },
    }
    {
        "hostname": "unisphere.lab.local"
        "powermax_serial": [
            "000011223344",
            "000055667788"
        ]
    },
]
```
For Kubernetes please create a corresponding secret and configmap entry for the variables, i.e. ```kubectl create secret generic powermax5678 --from-literal=password=”smc”```


### Run at the command line or use the provided docker start script
```
docker run \
	--publish 8080:8080 \
	--detach=true \
	--mount type=bind,source=./pmax_config.json,target=/pmaxperfpy/pmax_config.json,readonly \
	--name pmaxperfpy \
	pmaxperfpy:latest
```

#### Setup the target configuration for prometheus
* add the following section to your prometheus config, add collectors as targets
* for a new prometheus instance you can use the provided prometheus_config.yml example
```
- job_name: powermax
  honor_timestamps: true
  scrape_interval: 1m
  scrape_timeout: 50s
  metrics_path: /metrics
  scheme: http
  static_configs:
  - targets:
    - 192.168.1.1:8080
```

#### Import the provided dashboard into Grafana or create your own
* Before importing make sure Grafana has a datasource named Prometheus which is set as default datasource
* After the import datasource name and default setting can be changed again

### Setup Prometheus and Grafana
* can add into existing prometheus/grafana instances
* can use the provided scripts to start a grafana or prometheus instance

### Systemd startup scripts
* If no other container management is in place you can use the provided startup scripts
* For multiple collectors you need one startup script per collector instance
```
cp systemd_initscripts/docker-pmaxperfpy.service /etc/systemd/system/
cp systemd_initscripts/docker-grafana.service /etc/systemd/system/
cp systemd_initscripts/docker-prometheus.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable docker-pmaxperfpy.service
systemctl enable docker-grafana.service
systemctl enable docker-prometheus.service
```

### OpenTelemetry Setup

Please see the [OpenTelemetry README](OpenTelemetry/README.md) in the OpenTelemetry folder for information on the setup and configuration of the OpenTelemetry Collector for the PowerMax performance collector. 
