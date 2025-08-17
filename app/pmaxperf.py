#!/usr/bin/env python3
''' pmaxperf.py: collect performance metrics from Unisphere for Powermax/Vmax
'''
import argparse
import json
import logging
import random
import signal
import sys
import threading
import time

import PyU4V
import prometheus_client
from requests.exceptions import RequestException

from modules.config import Config
from modules.storagegroup import StorageGroup
from modules.volumes import Volumes

METRIC_CLASSES = {
    'StorageGroupCapacity': StorageGroup,
    'VolumesCapacity': Volumes
}


#
# signal_handler
def signal_handler(sig, frame):  # pylint: disable=unused-argument
    ''' handler for graceful exit
    '''
    logging.info('Stopping (takes a moment)')
    main_stop_event.set()


#
# create_metric_classes
def create_metric_classes(pmax, cfg):
    ''' create custom metric class instances '''
    cls_instances = []
    for key, cls_name in METRIC_CLASSES.items():
        if key in cfg["categories"]:
            cls_instances.append(cls_name(pmax, cfg, _metrics, metric_lock))
    return cls_instances


#
# connect_unisphere
def connect_unisphere(cfg, serial=None):
    ''' connect to unisphere '''
    logging.info("Connecting to %s %s", cfg['hostname'], serial if serial else '')
    con = PyU4V.U4VConn(
        username=cfg['username'],
        password=cfg['password'],
        server_ip=cfg['hostname'],
        port=cfg['unisphere_port'],
        array_id=serial,
        verify=cfg['verify']
    )
    return con


#
# verify_performance_registration
def verify_performance_registration(con) -> bool:
    ''' verify array is registered for performance '''
    if hasattr(con.performance, 'is_array_diagnostic_performance_registered'):
        result = con.performance.is_array_diagnostic_performance_registered()
        logging.debug("Powermax %s is registered for diagnostic performance collection: %s", con.array_id, result)
        return result
    return False


#
# initial_unisphere_connection
def initial_unisphere_connection(cfg):
    ''' Start the initial unisphere connection. A later on disconnect/reconnect
        will be handled automatically but the initial connection must work.
        And some additional setup stuff like getting the serials
    '''
    try:
        con = connect_unisphere(cfg)
    except RequestException as err:
        logging.error("Unisphere %s: %s", cfg["hostname"], str(err))
        return []

    array_list = con.common.get_array_list()
    con.close_session()
    logging.info("Unisphere %s found the following arrays: %s", cfg["hostname"], array_list)
    serials = array_list

    if not serials:
        msg = "Could not find any matching serial in Unisphere, please check configuration or remove the serial option to auto detect"
        logging.fatal(msg)
        sys.exit(msg)

    return serials


#
# reconnect_unisphere
def reconnect_unisphere(cfg, serial):
    ''' try to sleep and reconnect to unisphere (up to 10 times)
    '''
    retries = 1
    connected = False
    while retries < Config.RECONNECT_RETRY and not connected:
        logging.error("Lost connection to %s/%s, waiting %s seconds", cfg["hostname"], serial, config.RECONNECT_INTERVAL)
        time.sleep(config.RECONNECT_INTERVAL)
        try:
            pmaxcon = connect_unisphere(cfg, serial)
            connected = True
        except RequestException as err:
            logging.error("Reconnect %s/%s (%d) did not work: %s", cfg["hostname"], serial, retries, str(err))
            retries += 1
    if not connected:
        logging.critical("Failed to reconnect %s/%s too many times, bailing out.", cfg["hostname"], serial)
        return False
    return pmaxcon


#
# parse_metrics
def parse_metrics(pmax, base_tags):
    ''' collect and parse all metrics '''
    instance_count = 0
    all_metrics = pmax.performance_enhanced.get_all_performance_metrics_for_system()
    for category in all_metrics:
        tags = base_tags.copy()
        instance_count += len(category["metric_instances"])
        for instance in category["metric_instances"]:
            tags[category["id"]] = instance["id"]
            for key in instance["metrics"][0]:
                if key == "timestamp":
                    continue
                metric_name = "powermax_" + category["id"] + "_" + key
                if metric_name in _metrics:
                    p_metric = _metrics[metric_name]
                else:
                    with metric_lock:
                        p_metric = prometheus_client.Gauge(metric_name, '', labelnames=tags.keys())
                        _metrics[metric_name] = p_metric
                p_metric.labels(**tags).set_to_current_time()
                p_metric.labels(**tags).set(instance["metrics"][0][key])
    return (len(all_metrics), instance_count)


#
# run_thread_loop
def run_thread_loop(pmax, cfg, custom_metrics):
    ''' main thread loop for each powermax '''

    # use 10 seconds sleep internally to allow faster stopping of threads
    counter = cfg["interval"]
    while pmax and not main_stop_event.is_set():
        if counter < cfg["interval"]:
            counter += config.SLEEP
            time.sleep(config.SLEEP)
            continue
        counter = 0
        iteration_start = time.time()
        try:
            category_count = 0
            instance_count = 0
            for custom_cls in custom_metrics:
                (categories, instances) = custom_cls.parse_metrics()
                category_count += categories
                instance_count += instances

            (categories, instances) = parse_metrics(pmax, cfg["tags"])
            category_count += categories
            instance_count += instances

        except RequestException as err:
            logging.error("%s/%s error: %s", cfg["hostname"], cfg["serial"], str(err))
            pmax = reconnect_unisphere(cfg, cfg["serial"])

        # log time taken and sleep to align with the next interval
        duration = time.time() - iteration_start
        logging.info('%s: collected %d metric instances in %s categories in %2.3f seconds', cfg["serial"], instances, categories, duration)
        sleep_time = float(config.SLEEP - duration % config.SLEEP)
        counter += duration + sleep_time
        time.sleep(sleep_time)
    logging.info("%s stopping performance collection", cfg["serial"])


#
# thread_main
def thread_main(cfg, serial):
    ''' main thread for each powermax '''
    cfg["serial"] = serial
    cfg["tags"] = {"serial": serial}
    pmax = connect_unisphere(cfg, serial)
    details = pmax.common.get_array(serial)
    logging.debug("powermax %s details: %s", serial, json.dumps(details, indent=4))
    if verify_performance_registration(pmax):
        logging.info("Monitoring array serial=%s, model=%s, code=%s", details['symmetrixId'], details['model'], details['microcode'])
        time.sleep(random.randint(1, 5))
        run_thread_loop(pmax, cfg, create_metric_classes(pmax, cfg))
    else:
        logging.error("Powermax %s/%s not enabled for performance collection", cfg["hostname"], serial)


#
# command_line_args
def command_line_args():
    ''' retrieve command line args, if any '''
    parser = argparse.ArgumentParser(description='Collect PowerMax performance metrics')
    parser.add_argument('--config-file', help='configuration file name, default is pmax_config.json')
    parser.add_argument('--debug', help='enable debug logging', action='store_true')
    return parser.parse_args()


###################################################
# MAIN
###################################################
def main():
    ''' main program starts here '''

    # install graceful exit handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    random.seed()

    prometheus_client.start_http_server(config.cfg["defaults"]['exposed_port'])
    logging.info('Exposing data for prometheus at port %s', config.cfg["defaults"]['exposed_port'])

    threadlist = []
    for uni_cfg in config.cfg["unispheres"]:
        serials = initial_unisphere_connection(uni_cfg)
        for serial in serials:
            if "powermax_serial" not in uni_cfg or serial in uni_cfg["powermax_serial"]:
                pmax_cfg = uni_cfg.copy()
                trd = threading.Thread(target=thread_main, args=(pmax_cfg, serial))
                trd.start()
                threadlist.append(trd)

    for trd in threadlist:
        trd.join()
    logging.info('Stopped all')
    sys.exit(0)


if __name__ == '__main__':
    # initialize global variables
    args = command_line_args()

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', datefmt='%d.%m.%Y-%H:%M:%S', level=log_level)

    try:
        config = Config(args)
    except Exception as any_err:
        logging.fatal(any_err)
        sys.exit(1)
    _metrics = {}
    main_stop_event = threading.Event()
    metric_lock = threading.Lock()
    main()
