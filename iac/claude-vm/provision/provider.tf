provider "proxmox" {
  endpoint = var.proxmox_endpoint
  insecure = true # Allow self-signed certificate on Proxmox server

  api_token = var.proxmox_api_token

  ssh {
    agent    = true
    username = "opentofu"
  }
}
