output "vm_ips" {
  description = "Map of VM names to their IP addresses"
  value = {
    for name, vm in proxmox_virtual_environment_vm.vm :
    name => vm.ipv4_addresses != null ? (
      length(vm.ipv4_addresses) > 1 ? (
        length(vm.ipv4_addresses[1]) > 0 ? vm.ipv4_addresses[1][0] : null
      ) : null
    ) : null
  }
}

output "vm_info" {
  description = "Detailed VM information for inventory generation"
  value = {
    for name, vm in proxmox_virtual_environment_vm.vm :
    name => {
      vm_id        = vm.vm_id
      node         = vm.node_name
      ipv4_address = vm.ipv4_addresses != null ? (
        length(vm.ipv4_addresses) > 1 ? (
          length(vm.ipv4_addresses[1]) > 0 ? vm.ipv4_addresses[1][0] : null
        ) : null
      ) : null
      mac_address = try(vm.network_device[0].mac_address, null)
      status      = "running"
    }
  }
}

output "ansible_inventory" {
  description = "Ansible inventory in JSON format"
  value = jsonencode({
    all = {
      hosts = {
        for name, vm in proxmox_virtual_environment_vm.vm :
        name => {
          ansible_host = vm.ipv4_addresses != null ? (
            length(vm.ipv4_addresses) > 1 ? (
              length(vm.ipv4_addresses[1]) > 0 ? vm.ipv4_addresses[1][0] : null
            ) : null
          ) : null
          ansible_user            = var.cloud_init_user
          ansible_ssh_common_args = "-o StrictHostKeyChecking=accept-new"
          vm_id                   = vm.vm_id
          proxmox_node            = vm.node_name
        }
      }
      vars = {
        ansible_python_interpreter = "/usr/bin/python3"
      }
      children = {
        claude_dev_vms = {
          hosts = { for name, vm in proxmox_virtual_environment_vm.vm : name => {} }
        }
      }
    }
  })
}

output "cloud_init_user" {
  description = "The cloud-init user configured on VMs"
  value       = var.cloud_init_user
}
