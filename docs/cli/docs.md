> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

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