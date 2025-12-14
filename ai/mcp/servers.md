# MCP Servers

## [Context7](https://github.com/upstash/context7)

<details>
<summary><strong>Claude Code</strong></summary>

```sh
claude mcp add context7 -- npx -y @upstash/context7-mcp
```
</details>

<details>
<summary><strong>VS Code</strong></summary>

```jsonc
//  in .vscode/mcp.json
{
    "mcp": {
        "servers": {
            "context7": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"]
            }
        }
    }
}
```
</details>

<details>
<summary><strong>Google Antigravity</strong></summary>

```jsonc
// https://antigravity.google/docs/mcp
{
  "mcpServers": {
    "context7": {
      "serverUrl": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```
</details>

## [Playwright MCP](https://github.com/microsoft/playwright-mcp)

<details>
<summary><strong>Claude Code</strong></summary>

```sh
claude mcp add playwright npx @playwright/mcp@latest
```
</details>

<details>
<summary><strong>VS Code</strong></summary>

```sh
code --add-mcp '{"name":"playwright","command":"npx","args":["@playwright/mcp@latest"]}'
```
</details>

<details>
<summary><strong>Google Antigravity</strong></summary>

```jsonc
// https://antigravity.google/docs/mcp
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest"
      ]
    }
  }
}
```
</details>

## [Chrome Dev Tools](https://github.com/ChromeDevTools/chrome-devtools-mcp)

<details>
<summary><strong>Claude Code</strong></summary>

```sh
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
```
</details>

<details>
<summary><strong>VS Code</strong></summary>

```sh
code --add-mcp '{"name":"io.github.ChromeDevTools/chrome-devtools-mcp","command":"npx","args":["-y","chrome-devtools-mcp"],"env":{}}'
```
</details>

<details>
<summary><strong>Google Antigravity</strong></summary>

```jsonc
// https://antigravity.google/docs/mcp
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--browser-url=http://127.0.0.1:9222",
        "-y"
      ]
    }
  }
}
```
</details>

## [Github MCP](https://github.com/github/github-mcp-server)

<details>
<summary><strong>Claude Code</strong></summary>

```sh
# https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-claude.md

claude mcp add --transport http github https://api.githubcopilot.com/mcp -H "Authorization: Bearer $(grep GITHUB_PAT .env | cut -d '=' -f2)"
```
</details>

<details>
<summary><strong>VS Code</strong></summary>

```jsonc
// https://github.com/github/github-mcp-server?tab=readme-ov-file#install-in-github-copilot-on-vs-code

{
  "mcp": {
    "inputs": [
      {
        "type": "promptString",
        "id": "github_token",
        "description": "GitHub Personal Access Token",
        "password": true
      }
    ],
    "servers": {
      "github": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-e",
          "GITHUB_PERSONAL_ACCESS_TOKEN",
          "ghcr.io/github/github-mcp-server"
        ],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
        }
      }
    }
  }
}
```
</details>