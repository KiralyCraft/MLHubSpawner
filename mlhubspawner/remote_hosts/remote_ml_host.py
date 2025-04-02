from .remote_generic_host import RemoteGenericHost

from traitlets import  Unicode, Integer, Tuple, List

class RemoteMLHost(RemoteGenericHost):
    # CPU Model (e.g., "Intel Xeon", "AMD EPYC", etc.)
    cpu_model = Unicode(help="The CPU model").tag(config=True)
    
    # Number of CPU cores available
    cpu_cores = Integer(help="The number of CPU cores").tag(config=True)
    
    # Amount of RAM (you may specify the unit in the help text, e.g., GB)
    ram = Integer(help="The amount of RAM (e.g., in GB)").tag(config=True)
    
    # List of GPU models (e.g., ["NVIDIA Tesla V100", "NVIDIA Tesla P100"])
    gpu = List(Unicode(), help="List of GPU models").tag(config=True)
    
    # Storage configuration as a tuple (storage type and size)
    storage = List(Tuple(Unicode(), Integer()), help="Storage configuration as (type, size)").tag(config=True)