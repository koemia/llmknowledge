---
title: "EchoLeak (CVE-2025-32711) Explained for Non-Engineers"
description: "How one ordinary-looking email made Microsoft 365 Copilot leak data, with no click required. Rated 9.3/10. What it teaches about AI assistant security."
h1: "What was EchoLeak, and why does it matter?"
chapter: ch6
published: "2026-10-21"
related: [can-embeddings-be-reversed, openai-api-data-retention]
short: "EchoLeak (CVE-2025-32711), disclosed in June 2025, let an attacker get data out of Microsoft 365 Copilot by sending one ordinary-looking email. No click was needed. Copilot later pulled the email in as relevant material, followed instructions hidden in it, and leaked data through an image that loaded automatically. Microsoft rated it 9.3 out of 10 [1][2]. It was reported to Microsoft in January 2025 and fixed in May [3]."
sources:
  - text: "Microsoft Security Response Center, CVE-2025-32711."
    url: "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2025-32711"
  - text: "NVD, CVE-2025-32711."
    url: "https://nvd.nist.gov/vuln/detail/CVE-2025-32711"
  - text: "Reddy & Gujral, *EchoLeak: The First Real-World Zero-Click Prompt Injection Exploit in a Production LLM System*, 2025."
    url: "https://arxiv.org/abs/2509.10540"
  - text: "UK National Cyber Security Centre, *Prompt injection is not SQL injection (it may be worse)*, December 8, 2025."
    url: "https://www.ncsc.gov.uk/sites/default/files/pdfs/blog/prompt-injection-is-not-sql-injection.pdf"
  - text: "Meta, *Agents Rule of Two: A Practical Approach to AI Agent Security*, October 31, 2025."
    url: "https://ai.meta.com/blog/practical-ai-agent-security/"
---

## How it worked, step by step

1. **Retrieval:** The attacker's email sat in the victim's mailbox. When the user later asked Copilot something, the email was retrieved as relevant material.
2. **Assembly:** It was placed in the same working context as the user's confidential material.
3. **Presentation:** An image in Copilot's output loaded automatically, and that request carried data out to the attacker.

The attacker never broke into anything. They only had to get text in front of the AI.

## Why this is hard to fix

Microsoft had deployed a detector built specifically to catch prompt injection, and EchoLeak got past it [3]. The root problem is prompt injection. As the UK's National Cyber Security Centre puts it, current language models do not enforce a security boundary between instructions and data inside a prompt [4]. To the model, an email is more text, and text can carry instructions. So defenses belong in the system around the model, not in the model.

## What to check in your own AI tools

- Can one assistant or agent do all three at once: touch untrusted content (emails, web pages), read sensitive internal data, and communicate externally or change data? Meta's "Rule of Two" says to grant at most two of these at once; if all three are unavoidable, a human approves every step [5].
- Does the output load external images or links automatically?
- Are untrusted sources kept apart from confidential internal stores?
- Does the assistant hold only the permissions its task needs?

**Go deeper:** Chapter 6 walks the whole pipeline from an attacker's point of view. [Read Chapter 6 →](../ch6)
