from typing import Any, Dict, List, Optional
from .remote_hosts.remote_generic_host import RemoteGenericHost

class MachineManager:
    def __init__(self, remote_hosts: List[RemoteGenericHost]):
        self.remote_hosts = remote_hosts
        # Maps unique_identifier -> allocation details
        self.allocations: Dict[str, Dict[str, Any]] = {}
        # Maps hostname -> list of unique_identifiers allocated to that hostname
        self.hostname_allocations: Dict[str, List[str]] = {}

    def find_machine(self, chosen_machine_type: RemoteGenericHost, requested_shared_mode: bool) -> Optional[str]:
        """
        Return an available machine hostname for the given machine type and requested access mode.
        
        For an exclusive request (requested_shared_mode == False):
          - The machine is eligible if it is completely free (no allocations).
        
        For a shared request (requested_shared_mode == True):
          - The chosen machine type must support sharing.
          - A machine is eligible if none of its current allocations were taken exclusively.
          - Among eligible machines, the one with the fewest current allocations is returned.
        
        Note: This method must be called under an external mutex lock.
        """
        # For shared requests, ensure the machine type supports sharing.
        if requested_shared_mode and not chosen_machine_type.shared_access_enabled:
            return None

        if not requested_shared_mode:
            # Exclusive request: choose a hostname that is completely free.
            for hostname in chosen_machine_type.hostnames:
                if hostname not in self.hostname_allocations or not self.hostname_allocations[hostname]:
                    return hostname
            return None
        else:
            # Shared request: choose a hostname that has no exclusive allocation.
            selected_hostname = None
            min_alloc_count = float('inf')
            for hostname in chosen_machine_type.hostnames:
                uids = self.hostname_allocations.get(hostname, [])

                # Check if any allocation on this hostname was taken exclusively.
                exclusive_found = False
                for uid in uids:
                    if self.allocations[uid]['shared_access_enabled'] is False:
                        exclusive_found = True
                        break

                if exclusive_found:
                    continue  # This hostname is not eligible for shared access.

                alloc_count = len(uids)  # Could be zero.
                if alloc_count < min_alloc_count:
                    min_alloc_count = alloc_count
                    selected_hostname = hostname
            return selected_hostname

    def take_machine(self, chosen_machine_type: RemoteGenericHost, machine_ip_port: str, unique_identifier: str, requested_shared_mode: bool):
        """
        Reserve the machine (hostname) for the given unique identifier.
        
        For an exclusive request (requested_shared_mode == False):
          - The hostname must be completely free (no allocations).
        
        For a shared request (requested_shared_mode == True):
          - The chosen machine type must support sharing.
          - The hostname must not have any allocation that was taken exclusively.
        
        This function must be executed atomically (i.e. under an external mutex lock).
        """
        # For shared requests, the machine type must support sharing.
        if requested_shared_mode and not chosen_machine_type.shared_access_enabled:
            return False

        if not requested_shared_mode:
            # Exclusive request: ensure the hostname is completely free.
            if machine_ip_port in self.hostname_allocations and self.hostname_allocations[machine_ip_port]:
                return False
        else:
            # Shared request: ensure no exclusive allocation exists on this hostname.
            uids = self.hostname_allocations.get(machine_ip_port, [])
            for uid in uids:
                if self.allocations[uid]['shared_access_enabled'] is False:
                    return False

        # Register the allocation.
        self.allocations[unique_identifier] = {
            'machine': chosen_machine_type,
            'hostname': machine_ip_port,
            'shared_access_enabled': requested_shared_mode
        }

        # Update the hostname_allocations dictionary.
        if machine_ip_port not in self.hostname_allocations:
            self.hostname_allocations[machine_ip_port] = []
        self.hostname_allocations[machine_ip_port].append(unique_identifier)

        return True

    def release_machine(self, unique_identifier: str):
        """
        Release the allocation associated with the given unique identifier.
        This method removes the allocation from both the allocations and the hostname_allocations dictionaries.
        """
        if unique_identifier not in self.allocations:
            return

        allocation = self.allocations[unique_identifier]
        hostname = allocation['hostname']

        # Remove from the allocations dictionary.
        del self.allocations[unique_identifier]

        # Remove from the hostname_allocations dictionary.
        if hostname in self.hostname_allocations:
            if unique_identifier in self.hostname_allocations[hostname]:
                self.hostname_allocations[hostname].remove(unique_identifier)
            if not self.hostname_allocations[hostname]:
                del self.hostname_allocations[hostname]

    def get_available_types(self, user_privilege_level: int) -> List[RemoteGenericHost]:
        """
        Return a list of remote host types available to a user with the given privilege level.
        Machine types that require privileged access are only included if the user has sufficient privileges.
        """
        available = []
        for host in self.remote_hosts:
            if host.privileged_access_required and user_privilege_level < 1:
                continue
            available.append(host)
        return available
