```sh

# Homebrew
# https://brew.sh/

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

echo >> $HOME/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> $HOME/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Aerospace
# https://github.com/nikitabobko/AeroSpace

brew install --cask nikitabobko/tap/aerospace

# Nvm
# https://github.com/nvm-sh/nvm

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" 

nvm install 22.18.0
nvm use 22.18.0


# Setting up SSH Key

ssh-keygen -t ed25519 -C "{REPLACE_ME}"

# Git Config

git config --global user.email "me@davidgaribay.dev"
git config --global user.name "David Garibay" 

# usql
# https://github.com/xo/usql

brew install xo/xo/usql


# Github CLI
# https://cli.github.com/

brew install gh

# PNPM
# https://pnpm.io/installation

npm install -g pnpm@latest-10

# Bun
# https://bun.com/

curl -fsSL https://bun.sh/install | bash


# Astral
# https://docs.astral.sh/uv/

curl -LsSf https://astral.sh/uv/install.sh | sh


# Claude Code
# https://www.claude.com/product/claude-code

curl -fsSL https://claude.ai/install.sh | bash

```