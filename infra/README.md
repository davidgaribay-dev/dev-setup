# Claude Code Harness

Infrastructure orchestration for Claude development environments on Proxmox VE. Deploy Neo4j graph databases, Plane project management servers, and multiple Claude development VMs with a single command.

## Quick Start

```bash
# Install the harness CLI
cd orchestration
uv sync --dev

# Set required environment variables (see Environment Variables section)
export TF_VAR_proxmox_api_token="user@realm!token-name=token-secret"
export NEO4J_ADMIN_PASSWORD="your-secure-password"
export NEO4J_PASSWORD="your-secure-password"

# Deploy everything: Neo4j + Plane + 2 Claude VMs
uv run harness all -c 2

# Check status
uv run harness status

# Destroy everything
uv run harness all --destroy
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Proxmox VE (pve1)                             │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   neo4j-db      │  │  plane-server   │  │     Claude VMs          │  │
│  │   VM ID: 150    │  │   VM ID: 160    │  │   VM IDs: 200+          │  │
│  │   10.0.70.50    │  │   10.0.70.70    │  │   10.0.70.x (DHCP)      │  │
│  │                 │  │                 │  │                         │  │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────────────┐  │  │
│  │  │  Neo4j    │  │  │  │   Plane   │  │  │  │   Claude Code     │  │  │
│  │  │  Docker   │  │  │  │   Docker  │  │  │  │   + MCP Servers   │  │  │
│  │  │           │  │  │  │   Caddy   │  │  │  │   + Dev Tools     │  │  │
│  │  │  :7687    │  │  │  │   :443    │  │  │  │                   │  │  │
│  │  │  :7474    │  │  │  │   :80     │  │  │  │   Neo4j MCP ────────────┼──→ Neo4j
│  │  └───────────┘  │  │  └───────────┘  │  │  │   Plane MCP ────────────┼──→ Plane
│  └─────────────────┘  └─────────────────┘  │  └───────────────────┘  │  │
│                                            └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### System Requirements

- **Proxmox VE** instance with API access
- **Ubuntu 24.04 VM template** (ID: 100 by default)
- **Network bridge** configured (`vmbr1`)

### Required Tools

#### OpenTofu (Terraform alternative)

```bash
sudo snap install --classic opentofu
```

#### Ansible

```bash
# Install pipx if not already installed
sudo apt update
sudo apt install pipx
pipx ensurepath

# Install Ansible
pipx install --include-deps ansible
```

#### UV (Python package manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TF_VAR_proxmox_api_token` | Proxmox API token for authentication | `user@pam!terraform=xxxx-xxxx-xxxx` |

### Neo4j Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_ADMIN_PASSWORD` | Initial Neo4j admin password (set during first deploy) | `changeme` |
| `NEO4J_PASSWORD` | Neo4j connection password for MCP servers | `changeme` |

### Plane Variables

| Variable | Description | How to Generate |
|----------|-------------|-----------------|
| `PLANE_SECRET_KEY` | Plane application secret (64 hex chars) | `openssl rand -hex 32` |
| `PLANE_LIVE_SECRET_KEY` | Live server key (32 hex chars) | `openssl rand -hex 16` |
| `PLANE_POSTGRES_PASSWORD` | PostgreSQL database password | `openssl rand -base64 24` |
| `PLANE_RABBITMQ_PASSWORD` | RabbitMQ message queue password | `openssl rand -base64 24` |
| `PLANE_MINIO_ACCESS_KEY` | MinIO/S3 access key | Any string |
| `PLANE_MINIO_SECRET_KEY` | MinIO/S3 secret key | Any string |
| `CADDY_EMAIL` | Email for Caddy SSL certificates | `admin@example.com` |

### Claude VM Variables (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `ANSIBLE_GH_TOKEN` | GitHub token for gh CLI pre-authentication | None |
| `NEO4J_IP` | Override Neo4j IP address | `10.0.70.50` |
| `PLANE_IP` | Override Plane IP address | `10.0.70.70` |
| `PLANE_API_KEY` | Plane API key for MCP server | None |
| `PLANE_WORKSPACE_SLUG` | Plane workspace slug for MCP server | None |

### Example .env File

Create a `.env` file (do not commit to version control):

```bash
# Proxmox Authentication (REQUIRED)
export TF_VAR_proxmox_api_token="user@pam!terraform=your-token-here"

# Neo4j (REQUIRED for deployment)
export NEO4J_ADMIN_PASSWORD="super-secure-admin-password"
export NEO4J_PASSWORD="neo4j-connection-password"

# Plane (generate fresh values)
export PLANE_SECRET_KEY="$(openssl rand -hex 32)"
export PLANE_LIVE_SECRET_KEY="$(openssl rand -hex 16)"
export PLANE_POSTGRES_PASSWORD="$(openssl rand -base64 24)"
export PLANE_RABBITMQ_PASSWORD="$(openssl rand -base64 24)"
export PLANE_MINIO_ACCESS_KEY="plane-minio-access"
export PLANE_MINIO_SECRET_KEY="plane-minio-secret-key"
export CADDY_EMAIL="admin@yourdomain.com"

# GitHub (optional - for gh CLI on VMs)
export ANSIBLE_GH_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Plane MCP (optional - configure after Plane is running)
# export PLANE_API_KEY="your-api-key"
# export PLANE_WORKSPACE_SLUG="your-workspace"
```

Load it before running commands:

```bash
source .env
```

## CLI Commands

### Global Options

| Option | Description |
|--------|-------------|
| `--version, -V` | Show version and exit |
| `--verbose, -v` | Enable verbose output (debug logging) |
| `--json, -j` | Output results as JSON |

### Deploy Everything

```bash
# Deploy Neo4j + Plane + 1 Claude VM
harness all

# Deploy Neo4j + Plane + 3 Claude VMs
harness all -c 3

# Destroy everything (VMs first, then services)
harness all --destroy
```

### Individual Components

#### Neo4j

```bash
# Deploy Neo4j database
harness neo4j

# Destroy Neo4j
harness neo4j --destroy

# Re-run Ansible only (skip provisioning)
harness neo4j --skip-provision

# Provision only (skip configuration)
harness neo4j --skip-configure
```

#### Plane

```bash
# Deploy Plane project management
harness plane

# Destroy Plane
harness plane --destroy

# Re-run Ansible only
harness plane --skip-provision
```

#### Claude VMs

```bash
# Deploy 1 Claude VM
harness vms

# Deploy 3 Claude VMs
harness vms -c 3

# Deploy with custom prefix
harness vms -c 2 -p myproject

# Deploy with custom starting VM ID
harness vms -c 2 -s 300

# Skip hardening (faster iteration)
harness vms --skip-hardening

# Show plan without applying
harness vms --plan-only

# Destroy all Claude VMs
harness vms --destroy
```

### Check Status

```bash
harness status
```

## Project Structure

```
claude-code-harness/
├── README.md
├── orchestration/                 # Python CLI orchestration
│   ├── pyproject.toml             # Python project config
│   ├── config.yaml                # Central configuration
│   └── harness/
│       ├── cli/
│       │   ├── app.py             # Main Typer CLI
│       │   └── commands/          # Individual commands
│       │       ├── neo4j.py
│       │       ├── plane.py
│       │       ├── vms.py
│       │       ├── all_cmd.py
│       │       └── status.py
│       ├── core/
│       │   ├── config.py          # Configuration dataclasses
│       │   ├── context.py         # App context
│       │   ├── logger.py          # Logging utilities
│       │   └── runner.py          # Command execution
│       ├── deployers/
│       │   ├── base.py            # BaseDeployer abstract class
│       │   ├── neo4j.py           # Neo4j deployer
│       │   ├── plane.py           # Plane deployer
│       │   └── claude_vms.py      # Claude VMs deployer
│       └── infra/
│           ├── tofu.py            # OpenTofu manager
│           ├── ansible.py         # Ansible runner
│           └── ssh.py             # SSH utilities
│
├── neo4j/                         # Neo4j component
│   ├── provision/                 # OpenTofu configs
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── provider.tf
│   │   └── versions.tf
│   └── configuration/             # Ansible configs
│       ├── playbook.yml
│       ├── requirements.yml
│       ├── group_vars/all.yml
│       ├── inventory/             # Generated hosts.json
│       └── files/
│           └── docker-compose.yml.j2
│
├── plane/                         # Plane component
│   ├── provision/                 # OpenTofu configs
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── provider.tf
│   │   ├── versions.tf
│   │   └── terraform.tfvars
│   └── configuration/             # Ansible configs
│       ├── playbook.yml
│       ├── requirements.yml
│       ├── group_vars/all.yml
│       ├── inventory/
│       └── files/
│           ├── docker-compose.yml.j2
│           ├── plane.env.j2
│           └── Caddyfile.j2
│
└── claude-vms/                    # Claude VMs component
    ├── provision/                 # OpenTofu configs
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   ├── provider.tf
    │   ├── versions.tf
    │   └── terraform.tfvars
    └── configuration/             # Ansible configs
        ├── playbook.yml
        ├── requirements.yml
        ├── group_vars/all.yml
        ├── inventory/
        └── files/
            ├── hooks/
            │   └── single_command_enforcer.py
            ├── claude-settings.json
            └── claude.json
```

## Configuration

### Central Config: `orchestration/config.yaml`

```yaml
neo4j:
  ip: "10.0.70.50"
  bolt_port: 7687
  http_port: 7474
  username: "neo4j"
  vm_id: 150
  vm_name: "neo4j-db"

plane:
  ip: "10.0.70.70"
  http_port: 80
  https_port: 443
  vm_id: 160
  vm_name: "plane-server"

claude_vms:
  start_id: 200
  default_count: 1
  prefix: "claude-dev"

network:
  subnet: "10.0.70.0/24"
  gateway: "10.0.70.1"
  bridge: "vmbr1"

proxmox:
  node: "pve1"
  template_id: 100
  datastore_id: "local-lvm"

ssh:
  user: "dmg"
  cloud_init_user: "dmg"
  timeout: 300
  retry_interval: 10
```

### Terraform Variables: `*/provision/terraform.tfvars`

Each component has its own `terraform.tfvars` with:

- `proxmox_endpoint` - Proxmox API URL
- `proxmox_node` - Proxmox node name
- `template_id` - VM template to clone
- `datastore_id` - Storage datastore
- Hardware specs (CPU cores, memory)
- Network configuration

## What Gets Deployed

### Neo4j VM

- **VM**: Ubuntu 24.04, 2 cores, 4GB RAM
- **Software**: Docker, Neo4j Community Edition 5.x
- **Ports**: 7687 (Bolt), 7474 (HTTP Browser)
- **Access**: `http://10.0.70.50:7474` (Neo4j Browser)

### Plane VM

- **VM**: Ubuntu 24.04, 4 cores, 8GB RAM
- **Software**: Docker, Plane (13 containers), Caddy reverse proxy
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Access**: `https://10.0.70.70` (Plane Web UI)

### Claude VMs

- **VM**: Ubuntu 24.04, 4 cores, 8GB RAM each
- **Software**:
  - Docker
  - Claude Code CLI
  - Node.js (via NVM)
  - Python (via UV)
  - GitHub CLI
  - tea CLI (Gitea)
- **Security Hardening**:
  - OS hardening (devsec.hardening)
  - SSH hardening (key-only auth)
  - UFW firewall
  - fail2ban
  - Automatic security updates
- **MCP Servers** (pre-configured):
  - Context7 - Library documentation
  - Playwright - Browser automation
  - Neo4j Cypher - Graph database queries
  - Plane (optional) - Project management

## Security

### API Token Security

**Never commit API tokens to version control.** Use environment variables:

```bash
export TF_VAR_proxmox_api_token="user@realm!token-name=token-secret"
```

### TLS Certificate Verification

TLS verification is enabled by default. For self-signed certificates:
1. Add your Proxmox CA to the system trust store, or
2. Set `insecure = true` in `provider.tf` (not recommended)

### Verified External Sources

| Component | Source | Verification |
|-----------|--------|--------------|
| Docker | download.docker.com | GPG: `9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C 0EBF CD88` |
| GitHub CLI | cli.github.com | GPG: `2C61 0620 1985 B60E 6C7A C873 23F3 D4EA 7571 6059` |
| tea CLI | dl.gitea.com | SHA256 checksum |
| NVM | github.com/nvm-sh/nvm | Official repository |
| UV | astral.sh | Official source |
| Claude CLI | claude.ai | Official Anthropic source |

### Pinned Versions

- **OpenTofu Provider**: `bpg/proxmox = 0.93.0`
- **Ansible Collections**:
  - `devsec.hardening = 10.4.0`
  - `community.general = 10.2.0`
  - `ansible.posix = 2.0.0`
- **Ansible Roles**:
  - `geerlingguy.docker = 7.4.1`
- **Go**: Installed directly from `go.dev/dl/` (version defined in `group_vars/all.yml`)

### Claude Code Sandbox

Claude VMs are configured with sandbox mode:

- **Enabled**: OS-level filesystem and network isolation
- **Auto-approve bash**: Commands auto-approved within sandbox
- **Docker excluded**: Docker runs outside sandbox (incompatible)
- **Blocked directories**: `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.config/gh`
- **Blocked commands**: `curl`, `wget` (prevents data exfiltration)

## MCP Servers on Claude VMs

| Server | Command | Environment Variables |
|--------|---------|----------------------|
| Context7 | `npx -y @upstash/context7-mcp` | None |
| Playwright | `npx -y @playwright/mcp@latest` | None |
| Neo4j Cypher | `uvx mcp-neo4j-cypher@0.5.2` | `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` |
| Plane | `npx -y mcp-remote@latest` | `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG` |

Verify installed MCP servers:

```bash
claude mcp list
```

## Post-Deployment Setup

### Plane Initial Setup

After deploying Plane, complete the initial setup via the web UI:

1. Navigate to `https://10.0.70.70`
2. Complete the signup/onboarding wizard
3. Create a workspace
4. Generate an API key (Settings > API Tokens)

Then configure Claude VMs to use Plane MCP:

```bash
export PLANE_API_KEY="your-api-key"
export PLANE_WORKSPACE_SLUG="your-workspace"

# Redeploy Claude VMs to configure MCP
harness vms --skip-provision
```

### Neo4j Initial Setup

1. Navigate to `http://10.0.70.50:7474`
2. Login with `neo4j` / `NEO4J_ADMIN_PASSWORD`
3. Create databases, constraints, and data as needed

## Troubleshooting

### Common Issues

**OpenTofu fails with API token error:**
```bash
# Ensure token is exported
echo $TF_VAR_proxmox_api_token
# Should output your token
```

**Ansible can't connect to VMs:**
```bash
# Check VM is running in Proxmox
# Verify SSH key is configured in cloud-init template
# Try manual SSH: ssh dmg@<vm-ip>
```

**Neo4j container not starting:**
```bash
# SSH to Neo4j VM
ssh dmg@10.0.70.50
# Check Docker logs
docker logs neo4j
```

**Plane containers not healthy:**
```bash
# SSH to Plane VM
ssh dmg@10.0.70.70
# Check all containers
docker ps
# Check specific service logs
docker logs plane-api-1
```

### Verbose Output

Add `-v` for detailed logging:

```bash
harness -v all -c 2
```

### Re-run Configuration Only

If provisioning succeeded but configuration failed:

```bash
harness neo4j --skip-provision
harness plane --skip-provision
harness vms --skip-provision
```

### Skip Hardening (Faster Iteration)

During development, skip slow hardening tasks:

```bash
harness vms --skip-hardening
```

## Orchestration CLI

The `harness` CLI is a Python package built with [Typer](https://typer.tiangolo.com/) that orchestrates OpenTofu provisioning and Ansible configuration.

### Installation

```bash
cd orchestration

# Install with uv (recommended)
uv sync --dev

# Run commands with uv
uv run harness --help

# Or install globally with pipx
pipx install -e .
harness --help
```

### CLI Architecture

```
harness/
├── cli/
│   ├── app.py              # Main Typer app, global options
│   └── commands/           # Subcommands
│       ├── neo4j.py        # harness neo4j
│       ├── plane.py        # harness plane
│       ├── vms.py          # harness vms
│       ├── all_cmd.py      # harness all
│       └── status.py       # harness status
├── core/
│   ├── config.py           # Config dataclasses (Neo4jConfig, PlaneConfig, etc.)
│   ├── context.py          # AppContext passed to commands
│   ├── logger.py           # Rich console logging
│   ├── runner.py           # Subprocess execution
│   └── exitcodes.py        # Exit code constants
├── deployers/
│   ├── base.py             # BaseDeployer abstract class
│   ├── neo4j.py            # Neo4jDeployer
│   ├── plane.py            # PlaneDeployer
│   └── claude_vms.py       # ClaudeVMsDeployer
└── infra/
    ├── tofu.py             # OpenTofu wrapper (init, plan, apply, destroy)
    ├── ansible.py          # Ansible wrapper (galaxy install, playbook)
    └── ssh.py              # SSH connection testing
```

### Adding a New Component

To add a new deployable component (e.g., a Redis VM):

1. **Create infrastructure files:**
   ```
   redis/
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

2. **Add config dataclass** in `harness/core/config.py`:
   ```python
   @dataclass
   class RedisConfig:
       ip: str
       port: int
       vm_id: int
       vm_name: str
   ```

3. **Update Config class** to include the new component:
   ```python
   @dataclass
   class Config:
       redis: RedisConfig
       # ...

       @property
       def redis_dir(self) -> Path:
           return self.project_root / "redis"
   ```

4. **Create deployer** in `harness/deployers/redis.py`:
   ```python
   class RedisDeployer(BaseDeployer):
       @property
       def component_name(self) -> str:
           return "Redis Cache Server"

       @property
       def provision_dir(self) -> Path:
           return self.config.redis_dir / "provision"

       # Implement _provision, _configure, _destroy, _log_summary
   ```

5. **Create CLI command** in `harness/cli/commands/redis.py`:
   ```python
   def redis(
       ctx: typer.Context,
       destroy: bool = False,
       # ... options
   ) -> None:
       deployer = RedisDeployer(app_ctx.config, app_ctx.console)
       # ...
   ```

6. **Register command** in `harness/cli/app.py`:
   ```python
   from harness.cli.commands import redis
   app.command("redis")(redis)
   ```

7. **Update config.yaml** with the new component section.

### Deployer Pattern

All deployers inherit from `BaseDeployer` which provides:

- `deploy()` - Runs provision → configure
- `destroy()` - Destroys infrastructure
- Infrastructure managers: `self.tofu`, `self.ansible`, `self.ssh`
- Console output: `self.console`

Override these methods:
- `_provision()` - OpenTofu apply logic
- `_configure()` - Ansible playbook logic
- `_destroy()` - OpenTofu destroy logic
- `_log_summary()` - Post-deploy info (URLs, ports, etc.)

## Development

### Running Tests

```bash
cd orchestration
uv run pytest
```

### Type Checking

```bash
uv run mypy harness
```

### Linting

```bash
uv run ruff check harness
uv run ruff format harness
```

### Pre-commit Checks

```bash
cd orchestration
uv run ruff check harness && uv run ruff format --check harness && uv run mypy harness && uv run pytest
```

## License

MIT License - See pyproject.toml for details.
