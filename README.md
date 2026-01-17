# dev-setup

Personal development environment configuration including infrastructure as code and container definitions.

## Contents

- [iac/](iac/) - Infrastructure as Code for development VMs
- [vms/](vms/) - Virtual machine configurations for self-hosted services

## Infrastructure as Code

### Claude Development VM
- [claude-vm](iac/claude-vm/) - Automated provisioning of Claude Code development VMs on Proxmox VE
  - OpenTofu/Terraform for VM provisioning
  - Ansible for configuration management
  - Pre-configured with Claude Code, MCP servers, and security hardening

## Self-Hosted Services

### Gitea VM
- [Gitea](vms/gitea-vm/gitea/) - Self-hosted Git server with CI/CD runners

### Services VM
- [Baserow](vms/services-vm/baserow/) - No-code database platform
- [Draw.io](vms/services-vm/drawio/) - Diagramming application
- [Plane](vms/services-vm/plane/) - Project management platform

> **Note:** Replace all `{REPLACE_ME}` values in config files with your actual IP addresses or domains before deploying.

## License

MIT
