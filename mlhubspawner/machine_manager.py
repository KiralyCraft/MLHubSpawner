class MachineManager():
    def __init__(self, remote_hosts):
        self.remote_hosts = remote_hosts

    def find_machine(self, machine_select, exclusive_access_desired):
        # Check if the selected index is valid
        if machine_select < 0 or machine_select >= len(self.remote_hosts):
            return (None, None)

        # Get the selected machine
        selected_host = self.remote_hosts[machine_select]

        

        # Return the hostname and port (ignoring exclusive_access_desired for now)
        return (None, None)