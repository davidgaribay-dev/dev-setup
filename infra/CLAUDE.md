# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code Harness is an infrastructure orchestration tool for deploying Claude development environments on Proxmox VE. It provisions and configures:
- **Neo4j database server** - Shared graph database with MCP integration (Docker-based)
- **Plane project management server** - Self-hosted Plane instance with MCP integration (Docker + Caddy)
- **Claude development VMs** - Ephemeral sandboxed environments with Claude Code CLI pre-installed

## Architecture

```
claude-code-harness/
├── orchestration/           # Python CLI (harness)
│   ├── harness/
│   │   ├── cli/             # Typer CLI commands
│   │   ├── core/            # Config, logging, runner
│   │   ├── deployers/       # BaseDeployer + Neo4j/Plane/ClaudeVMs implementations
│   │   └── infra/           # OpenTofu, Ansible, SSH managers
│   ├── tests/
│   └── config.yaml          # Central configuration
├── neo4j/                   # Neo4j VM provisioning
│   ├── provision/           # OpenTofu/Terraform configs
│   └── configuration/       # Ansible playbooks + Docker Compose
├── plane/                   # Plane VM provisioning
│   ├── provision/           # OpenTofu/Terraform configs
│   └── configuration/       # Ansible playbooks + Docker Compose + Caddy
└── claude-vms/              # Claude VM provisioning
    ├── provision/           # OpenTofu/Terraform configs
    └── configuration/       # Ansible playbooks
```

The CLI orchestrates a two-phase deployment per component:
1. **Provision** (OpenTofu) → Creates VMs on Proxmox, exports inventory to `configuration/inventory/hosts.json`
2. **Configure** (Ansible) → Installs software, applies security hardening

## Common Commands

### CLI Usage

```bash
cd orchestration

# Install in development mode
uv sync --dev

# Run the CLI
uv run harness --help
uv run harness all -c 2        # Deploy Neo4j + Plane + 2 Claude VMs
uv run harness neo4j           # Deploy Neo4j only
uv run harness plane           # Deploy Plane only
uv run harness vms -c 3        # Deploy 3 Claude VMs only
uv run harness status          # Check deployment status
uv run harness all --destroy   # Tear down everything
```

### Testing

```bash
cd orchestration

# Run all tests with coverage
uv run pytest

# Run a single test file
uv run pytest tests/test_cli.py

# Run a specific test
uv run pytest tests/test_cli.py::TestCLIHelp::test_help_shows_commands -v
```

### Linting and Type Checking

```bash
cd orchestration

uv run ruff check .            # Lint
uv run ruff check . --fix      # Lint with auto-fix
uv run ruff format .           # Format
uv run mypy harness            # Type check

# All checks in one command
uv run ruff check harness && uv run ruff format --check harness && uv run mypy harness && uv run pytest
```

## Key Patterns

### Deployer Pattern

All component deployers inherit from `BaseDeployer` (`harness/deployers/base.py`):
- Implements `deploy()` and `destroy()` orchestration
- Abstract methods: `_provision()`, `_configure()`, `_destroy()`, `_log_summary()`
- Uses `OpenTofuManager`, `AnsibleManager`, `SSHWaiter` from `harness/infra/`

### Configuration Flow

1. `config.yaml` is loaded by `Config.from_yaml()` in `harness/core/config.py`
2. `AppContext` wraps config + logger for CLI commands
3. Deployers receive config and generate OpenTofu `-var` arguments dynamically

### Environment Variables

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `TF_VAR_proxmox_api_token` | Proxmox API authentication | All deployments |
| `NEO4J_ADMIN_PASSWORD` | Initial Neo4j admin password | Neo4j deployment |
| `NEO4J_PASSWORD` | Neo4j MCP connection password | Claude VMs |
| `PLANE_SECRET_KEY` | Plane application secret | Plane deployment |
| `PLANE_LIVE_SECRET_KEY` | Plane live server key | Plane deployment |
| `PLANE_POSTGRES_PASSWORD` | Plane PostgreSQL password | Plane deployment |
| `PLANE_RABBITMQ_PASSWORD` | Plane RabbitMQ password | Plane deployment |
| `PLANE_MINIO_ACCESS_KEY` | Plane MinIO access key | Plane deployment |
| `PLANE_MINIO_SECRET_KEY` | Plane MinIO secret key | Plane deployment |
| `CADDY_EMAIL` | Caddy SSL certificate email | Plane deployment |
| `PLANE_API_KEY` | Plane MCP API key | Claude VMs (optional) |
| `PLANE_WORKSPACE_SLUG` | Plane workspace slug | Claude VMs (optional) |
| `ANSIBLE_GH_TOKEN` | GitHub CLI authentication | Claude VMs (optional) |

## Component Details

### Neo4j (VM ID: 150, IP: 10.0.70.50)
- Docker-based deployment with Neo4j Community Edition 5.x
- Ports: 7687 (Bolt), 7474 (HTTP Browser)
- Access: `http://10.0.70.50:7474`

### Plane (VM ID: 160, IP: 10.0.70.70)
- Docker Compose with 13 services + Caddy reverse proxy
- Ports: 80 (HTTP), 443 (HTTPS)
- Access: `https://10.0.70.70`

### Claude VMs (VM IDs: 200+, IPs: DHCP)
- Security hardening (devsec.hardening)
- Pre-installed: Docker, Claude Code CLI, Node.js, Python, GitHub CLI
- MCP servers: Context7, Playwright, Neo4j Cypher, Plane (optional)

## Adding a New MCP Server

Edit `claude-vms/configuration/playbook.yml`, add a task in the "Setup development environment for user" play:

```yaml
- name: Add <name> MCP server
  ansible.builtin.shell: |
    export PATH="{{ dev_user_home }}/.local/bin:$PATH"
    source {{ dev_user_home }}/.nvm/nvm.sh
    claude mcp add <name> --scope user -- npx -y <package>
  args:
    executable: /bin/bash
  become: true
  become_user: "{{ dev_user }}"
```

For MCP servers requiring environment variables:

```yaml
- name: Add <name> MCP server with env vars
  ansible.builtin.shell: |
    export PATH="{{ dev_user_home }}/.local/bin:$PATH"
    source {{ dev_user_home }}/.nvm/nvm.sh
    claude mcp add <name> --scope user -- <command>
  args:
    executable: /bin/bash
  environment:
    VAR_NAME: "{{ var_value }}"
  become: true
  become_user: "{{ dev_user }}"
  when: var_value | length > 0
```

## Adding a New Deployable Component

1. Create infrastructure files:
   ```
   <component>/
   ├── provision/
   │   ├── main.tf
   │   ├── variables.tf
   │   ├── outputs.tf
   │   ├── provider.tf
   │   └── versions.tf
   └── configuration/
       ├── playbook.yml
       ├── requirements.yml
       └── group_vars/all.yml
   ```

2. Add config dataclass in `harness/core/config.py`

3. Create deployer in `harness/deployers/<component>.py`

4. Create CLI command in `harness/cli/commands/<component>.py`

5. Register in `harness/cli/commands/__init__.py` and `harness/cli/app.py`

6. Update `orchestration/config.yaml`

## Adding a New CLI Command

1. Create command function in `harness/cli/commands/<name>.py`
2. Export from `harness/cli/commands/__init__.py`
3. Register in `harness/cli/app.py`: `app.command("<name>")(<function>)`
4. Add tests in `tests/test_cli.py`
