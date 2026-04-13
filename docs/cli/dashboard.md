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

# dashboard

# `openclaw dashboard`

Open the Control UI using your current auth.

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
openclaw dashboard
openclaw dashboard --no-open
```

Notes:

* `dashboard` resolves configured `gateway.auth.token` SecretRefs when possible.
* For SecretRef-managed tokens (resolved or unresolved), `dashboard` prints/copies/opens a non-tokenized URL to avoid exposing external secrets in terminal output, clipboard history, or browser-launch arguments.
* If `gateway.auth.token` is SecretRef-managed but unresolved in this command path, the command prints a non-tokenized URL and explicit remediation guidance instead of embedding an invalid token placeholder.


Built with [Mintlify](https://mintlify.com).