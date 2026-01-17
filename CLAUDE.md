# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Overview

This is a personal development environment configuration repository containing:
- Infrastructure as Code (IaC) for provisioning development VMs
- Docker Compose configurations for self-hosted services

## Directory Structure

```
dev-setup/
├── iac/                    # Infrastructure as Code
│   └── claude-vm/          # Claude development VM provisioning
│       ├── deploy.py       # Main deployment script
│       ├── provision/      # OpenTofu/Terraform configs
│       └── configuration/  # Ansible playbooks and configs
└── vms/                    # Self-hosted service configurations
    ├── gitea-vm/           # Gitea Git server
    └── services-vm/        # Various services (Baserow, Draw.io, Plane)
```

## Key Technologies

- **OpenTofu/Terraform**: VM provisioning on Proxmox VE
- **Ansible**: Configuration management and security hardening
- **Docker Compose**: Service container orchestration

## Claude VM (iac/claude-vm/)

The claude-vm directory contains automation for provisioning secure development VMs with:

### Pre-installed Tools
- Claude Code CLI with sandbox mode enabled
- Node.js (via NVM) with pnpm
- Python tooling (UV)
- Docker
- GitHub CLI (gh)

### MCP Servers (Pre-configured)
- **Context7**: Library documentation lookup (`npx -y @upstash/context7-mcp`)
- **Playwright**: Browser automation (`npx -y @playwright/mcp@latest`)

### Security Features
- OS hardening via devsec.hardening
- SSH hardening (key-only auth, modern ciphers)
- UFW firewall (deny incoming by default)
- fail2ban for brute-force protection
- Claude Code sandbox mode with permission restrictions

### Deployment Commands
```bash
cd iac/claude-vm

# Deploy a VM
./deploy.py

# Deploy multiple VMs
./deploy.py -c 3

# Skip SSH hardening (faster, for iteration)
./deploy.py --skip-hardening

# Destroy VMs
./deploy.py --destroy
```

## Self-Hosted Services (vms/)

Docker Compose configurations for various services. Each service directory contains:
- `docker-compose.yml` - Container definitions
- `README.md` - Service-specific documentation

### Services
- **Gitea**: Self-hosted Git with CI/CD
- **Baserow**: No-code database
- **Draw.io**: Diagramming tool
- **Plane**: Project management

## Common Tasks

### Adding a New MCP Server to Claude VM
Edit `iac/claude-vm/configuration/playbook.yml` and add a new task in the "Setup development environment for user" play:
```yaml
- name: Add <name> MCP server
  ansible.builtin.shell: |
    export PATH="{{ dev_user_home }}/.local/bin:$PATH"
    source {{ dev_user_home }}/.nvm/nvm.sh
    claude mcp add <name> --scope user -- npx -y <package>
  args:
    executable: /bin/bash
```

### Updating Ansible Variables
Edit `iac/claude-vm/configuration/group_vars/all.yml` for:
- Development packages to install
- Git configuration
- Tool versions (NVM, etc.)
- Security hardening settings

### Updating Terraform Variables
Edit `iac/claude-vm/provision/terraform.tfvars` for:
- Proxmox endpoint and node
- VM resources (CPU, memory)
- Network configuration
