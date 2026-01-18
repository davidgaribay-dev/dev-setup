locals {
  use_dhcp = var.ip_address == "dhcp"
}

resource "proxmox_virtual_environment_vm" "vm" {
  for_each = var.vms

  name        = each.key
  node_name   = var.proxmox_node
  description = "Cloned from template ${var.template_id} via OpenTofu"
  vm_id       = each.value.vm_id

  clone {
    vm_id        = var.template_id
    full         = true
    datastore_id = var.datastore_id
    retries      = 3
  }

  cpu {
    cores   = coalesce(each.value.cpu_cores, var.cpu_cores)
    sockets = 1
    type    = "host"
  }

  memory {
    dedicated = coalesce(each.value.memory, var.memory)
  }

  initialization {
    datastore_id = var.datastore_id

    dns {
      servers = var.dns_servers
    }

    ip_config {
      ipv4 {
        address = coalesce(each.value.ip_address, var.ip_address)
        gateway = local.use_dhcp ? null : var.gateway
      }
    }

    user_account {
      username = var.cloud_init_user
    }
  }

  network_device {
    bridge = var.network_bridge
  }

  agent {
    enabled = true
  }

  started         = true
  stop_on_destroy = true

  lifecycle {
    ignore_changes = [
      initialization,
    ]
  }
}