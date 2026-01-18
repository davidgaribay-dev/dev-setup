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

variable "vm_id" {
  description = "VM ID for the Core Services server"
  type        = number
  default     = 160
}

variable "vm_name" {
  description = "Name of the Core Services VM"
  type        = string
  default     = "core-services"
}

variable "cpu_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 4
}

variable "memory" {
  description = "Memory in MB"
  type        = number
  default     = 8192
}

variable "network_bridge" {
  description = "Proxmox network bridge to attach VM to"
  type        = string
  default     = "vmbr1"
}

variable "ip_address" {
  description = "Static IP address in CIDR notation (e.g., '10.0.70.70/24')"
  type        = string
  default     = "10.0.70.70/24"
}

variable "gateway" {
  description = "Network gateway"
  type        = string
  default     = "10.0.70.1"
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
