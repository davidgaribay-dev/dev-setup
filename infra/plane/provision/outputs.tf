output "plane_ip" {
  description = "IP address of the Plane server (without CIDR suffix)"
  value       = split("/", var.ip_address)[0]
}

output "plane_vm_info" {
  description = "Detailed Plane VM information"
  value = {
    vm_id        = proxmox_virtual_environment_vm.plane.vm_id
    vm_name      = proxmox_virtual_environment_vm.plane.name
    node         = proxmox_virtual_environment_vm.plane.node_name
    ipv4_address = split("/", var.ip_address)[0]
    mac_address  = try(proxmox_virtual_environment_vm.plane.network_device[0].mac_address, null)
    status       = "running"
  }
}

output "ansible_inventory" {
  description = "Ansible inventory in JSON format"
  value = jsonencode({
    all = {
      hosts = {
        (var.vm_name) = {
          ansible_host            = split("/", var.ip_address)[0]
          ansible_user            = var.cloud_init_user
          ansible_ssh_common_args = "-o StrictHostKeyChecking=accept-new"
          vm_id                   = proxmox_virtual_environment_vm.plane.vm_id
          proxmox_node            = proxmox_virtual_environment_vm.plane.node_name
        }
      }
      vars = {
        ansible_python_interpreter = "/usr/bin/python3"
      }
      children = {
        plane_servers = {
          hosts = {
            (var.vm_name) = {}
          }
        }
      }
    }
  })
}

output "cloud_init_user" {
  description = "The cloud-init user configured on the VM"
  value       = var.cloud_init_user
}

output "http_uri" {
  description = "HTTP connection URI for Plane"
  value       = "http://${split("/", var.ip_address)[0]}"
}

output "https_uri" {
  description = "HTTPS connection URI for Plane"
  value       = "https://${split("/", var.ip_address)[0]}"
}
