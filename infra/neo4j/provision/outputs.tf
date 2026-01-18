output "neo4j_ip" {
  description = "IP address of the Neo4j server (without CIDR suffix)"
  value       = split("/", var.ip_address)[0]
}

output "neo4j_vm_info" {
  description = "Detailed Neo4j VM information"
  value = {
    vm_id        = proxmox_virtual_environment_vm.neo4j.vm_id
    vm_name      = proxmox_virtual_environment_vm.neo4j.name
    node         = proxmox_virtual_environment_vm.neo4j.node_name
    ipv4_address = split("/", var.ip_address)[0]
    mac_address  = try(proxmox_virtual_environment_vm.neo4j.network_device[0].mac_address, null)
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
          vm_id                   = proxmox_virtual_environment_vm.neo4j.vm_id
          proxmox_node            = proxmox_virtual_environment_vm.neo4j.node_name
        }
      }
      vars = {
        ansible_python_interpreter = "/usr/bin/python3"
      }
      children = {
        neo4j_servers = {
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

output "bolt_uri" {
  description = "Bolt connection URI for Neo4j"
  value       = "bolt://${split("/", var.ip_address)[0]}:7687"
}

output "http_uri" {
  description = "HTTP connection URI for Neo4j Browser"
  value       = "http://${split("/", var.ip_address)[0]}:7474"
}
