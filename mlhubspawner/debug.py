#!/usr/bin/env python

from traitlets.config import Configurable, Config
from traitlets import List, Instance, TraitError
from remote_hosts.remote_ml_host import RemoteMLHost
from config_parsers import DictionaryInstanceParser

class MLHostSpawner(Configurable):
    # Use the custom trait to allow conversion from dict to RemoteMLHost.
    remote_hosts = List(DictionaryInstanceParser(RemoteMLHost), help="Possible remote hosts from which to choose remote_host.", config=True)

if __name__ == "__main__":
    # Simulate a configuration file loaded as a Config object.
    config = Config()
    
    # Wrap the MLHostSpawner configuration in a Config instance.
    spawner_config = Config()
    spawner_config.remote_hosts = [
        {
            "hostname": "192.168.1.100",
            "port": 9000,
            "total_instances": 1,
            "exclusive_access_enabled": False,
            "cpu_model": "Intel Xeon",
            "cpu_cores": 16,
            "ram": 64,
            "gpu": ["NVIDIA Tesla V100", "NVIDIA Tesla P100"],
            "storage": ("SSD", 1024)
        },
        {
            "hostname": "192.168.1.101",
            "port": 9001,
            "total_instances": 2,
            "exclusive_access_enabled": True,
            "cpu_model": "AMD EPYC",
            "cpu_cores": 32,
            "ram": 128,
            "gpu": ["NVIDIA Tesla A100"],
            "storage": ("NVMe", 2048)
        },
    ]
    config.MLHostSpawner = spawner_config
    
    # Instantiate the spawner with the configuration.
    spawner = MLHostSpawner(config=config)
    
    print("Testing MLHostSpawner with remote_hosts:")
    for host in spawner.remote_hosts:
        print(f"ML Host: {host.hostname}:{host.port}")
        print(f"   CPU: {host.cpu_model} ({host.cpu_cores} cores)")
        print(f"   RAM: {host.ram}GB")
        print(f"   GPUs: {host.gpu}")
        print(f"   Storage: {host.storage}")
        print(f"   Instances: {host.total_instances}, Exclusive Access: {host.exclusive_access_enabled}\n")
