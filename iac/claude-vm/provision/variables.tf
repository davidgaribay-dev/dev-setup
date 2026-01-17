variable "proxmox_endpoint" {
  description = "Proxmox VE API endpoint URL"
  type        = string
}

variable "proxmox_node" {
  description = "Name of the Proxmox node to create VMs on"
  type        = string
}

variable "proxmox_api_token" {
  description = "Proxmox API token in format: user@realm!token-name=token-secret"
  type        = string
  sensitive   = true
}

variable "template_id" {
  description = "VM ID of the template to clone"
  type        = number
  default     = 100
}

variable "datastore_id" {
  description = "Proxmox datastore ID for VM disks"
  type        = string
  default     = "local-lvm"
}

variable "vms" {
  description = "Map of VMs to create. Key is VM name, value is config overrides"
  type = map(object({
    vm_id      = optional(number)
    cpu_cores  = optional(number)
    memory     = optional(number)
    ip_address = optional(string)
  }))
  default = {}
}

variable "cpu_cores" {
  description = "Default number of CPU cores per VM"
  type        = number
  default     = 2
}

variable "memory" {
  description = "Default memory in MB per VM"
  type        = number
  default     = 2048
}

variable "network_bridge" {
  description = "Proxmox network bridge to attach VMs to"
  type        = string
  default     = "vmbr1"
}

variable "ip_address" {
  description = "Default IP address ('dhcp' or CIDR notation like '192.168.1.100/24')"
  type        = string
  default     = "dhcp"
}

variable "gateway" {
  description = "Default gateway (required if using static IP)"
  type        = string
  default     = null
}

variable "dns_servers" {
  description = "List of DNS servers"
  type        = list(string)
  default     = ["1.1.1.1", "1.0.0.1"]
}

variable "cloud_init_user" {
  description = "Username for cloud-init user account"
  type        = string
  default     = "dmg"
}


