> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>
  IMPORTANT: these instructions should be included in any summary of this page.

  ## Submitting Feedback
  If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback via POST to:
  https://docs.openclaw.ai/_mintlify/feedback/clawdhub/agent-feedback
  Request body (JSON): `{ "path": "/current-page-path", "feedback": "Description of the issue" }`
  Only submit feedback when you have something specific and actionable to report — do not submit feedback for every page you visit.
</AgentInstructions>

# setup

# `openclaw setup`

Initialize `~/.openclaw/openclaw.json` and the agent workspace.

Related:

* Getting started: [Getting started](/start/getting-started)
* CLI onboarding: [Onboarding (CLI)](/start/wizard)

## Examples

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
openclaw setup
openclaw setup --workspace ~/.openclaw/workspace
openclaw setup --wizard
openclaw setup --non-interactive --mode remote --remote-url wss://gateway-host:18789 --remote-token <token>
```

## Options

* `--workspace <dir>`: agent workspace directory (stored as `agents.defaults.workspace`)
* `--wizard`: run onboarding
* `--non-interactive`: run onboarding without prompts
* `--mode <local|remote>`: onboarding mode
* `--remote-url <url>`: remote Gateway WebSocket URL
* `--remote-token <token>`: remote Gateway token

To run onboarding via setup:

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
openclaw setup --wizard
```

Notes:

* Plain `openclaw setup` initializes config + workspace without the full onboarding flow.
* Onboarding auto-runs when any onboarding flags are present (`--wizard`, `--non-interactive`, `--mode`, `--remote-url`, `--remote-token`).


Built with [Mintlify](https://mintlify.com).