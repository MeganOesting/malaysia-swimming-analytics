## GitHub Copilot Chat

- Extension Version: 0.32.4 (prod)
- VS Code: vscode/1.105.1
- OS: Windows

## Network

User Settings:
```json
  "github.copilot.advanced.debug.useElectronFetcher": true,
  "github.copilot.advanced.debug.useNodeFetcher": false,
  "github.copilot.advanced.debug.useNodeFetchFetcher": true
```

Connecting to https://api.github.com:
- DNS ipv4 Lookup: 140.82.116.5 (177 ms)
- DNS ipv6 Lookup: Error (178 ms): getaddrinfo ENOTFOUND api.github.com
- Proxy URL: None (11 ms)
- Electron fetch (configured): HTTP 200 (180 ms)
- Node.js https: HTTP 200 (542 ms)
- Node.js fetch: HTTP 200 (636 ms)

Connecting to https://api.individual.githubcopilot.com/_ping:
- DNS ipv4 Lookup: 140.82.113.21 (176 ms)
- DNS ipv6 Lookup: Error (196 ms): getaddrinfo ENOTFOUND api.individual.githubcopilot.com
- Proxy URL: None (2 ms)
- Electron fetch (configured): HTTP 200 (891 ms)
- Node.js https: HTTP 200 (716 ms)
- Node.js fetch: HTTP 200 (729 ms)

## Documentation

In corporate networks: [Troubleshooting firewall settings for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/troubleshooting-firewall-settings-for-github-copilot).