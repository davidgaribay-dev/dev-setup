# Ubuntu Setup

## [Vim](https://www.vim.org/)

```sh
sudo apt install vim
```

## [NVM](https://github.com/nvm-sh/nvm)

```sh
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

nvm install 22.18.0
nvm use 22.18.0
```

## [PNPM](https://pnpm.io/installation)

```sh
npm install -g pnpm@latest-10
```

## [Claude Code](https://www.claude.com/product/claude-code)

```sh
curl -fsSL https://claude.ai/install.sh | bash
```

## [Github CLI](https://cli.github.com/)

```sh
sudo apt update
sudo apt install gh
```

## [Astral](https://docs.astral.sh/uv/)

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## [Docker](https://docs.docker.com/engine/install/ubuntu/)

```sh
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Post-installation steps
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

## Git Config

```sh
git config --global user.name "David Garibay"
git config --global user.email "me@davidgaribay.dev"
```

## [Setting up SSH Key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)

```sh
ssh-keygen -t ed25519 -C "{REPLACE_ME}"
```
