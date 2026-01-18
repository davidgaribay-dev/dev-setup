resource "proxmox_virtual_environment_vm" "neo4j" {
  name        = var.vm_name
  node_name   = var.proxmox_node
  description = "Neo4j database server - cloned from template ${var.template_id} via OpenTofu"
  vm_id       = var.vm_id

  clone {
    vm_id        = var.template_id
    full         = true
    datastore_id = var.datastore_id
    retries      = 3
  }

  cpu {
    cores   = var.cpu_cores
    sockets = 1
    type    = "host"
  }

  memory {
    dedicated = var.memory
  }

  initialization {
    datastore_id = var.datastore_id

    dns {
      servers = var.dns_servers
    }

    ip_config {
      ipv4 {
        address = var.ip_address
        gateway = var.gateway
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
