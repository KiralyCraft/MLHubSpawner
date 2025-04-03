from .remote_hosts.remote_generic_host import RemoteGenericHost

class MachineManager():
    def __init__(self, remote_hosts : list):
        self.remote_hosts = remote_hosts

    def find_machine(self, chosen_machine_type : RemoteGenericHost, shared_access_enabled : bool):
               
        return None

    def take_machine(self, chosen_machine_type : RemoteGenericHost, machine_ip_port : str, unique_identifier : str, shared_access_enabled : bool):
        pass
    
    def release_machine(self, unique_identifier : str):
        pass
    
    def get_available_types(self, user_privilege_level : int):
        return self.remote_hosts