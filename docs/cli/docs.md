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

# docs

# `openclaw docs`

Search the live docs index.

Arguments:

* `[query...]`: search terms to send to the live docs index

Examples:

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
openclaw docs
openclaw docs browser existing-session
openclaw docs sandbox allowHostControl
openclaw docs gateway token secretref
```

Notes:

* With no query, `openclaw docs` opens the live docs search entrypoint.
* Multi-word queries are passed through as one search request.


Built with [Mintlify](https://mintlify.com).