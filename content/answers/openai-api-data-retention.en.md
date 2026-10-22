---
title: "Does the OpenAI API Store Your Prompts? Training vs. Retention"
description: "OpenAI's API hasn't trained on customer data by default since March 2023, but abuse-monitoring logs can keep prompts for up to 30 days. Two separate promises."
h1: "Does the OpenAI API store my prompts?"
chapter: ch5
published: "2026-10-21"
related: [can-embeddings-be-reversed, echoleak-explained]
short: "It doesn't train on them by default, but it can keep them. OpenAI's API has not trained on customer data by default since March 2023. Separately, abuse-monitoring logs may include prompts and responses and be kept for up to 30 days. Turning that off requires Zero Data Retention, which needs OpenAI's approval in advance [1]."
sources:
  - text: "OpenAI, *Data controls in the OpenAI platform* (official documentation)."
    url: "https://developers.openai.com/api/docs/guides/your-data"
  - text: "OpenAI, *Prompt caching* (official documentation)."
    url: "https://developers.openai.com/api/docs/guides/prompt-caching"
---

## Two different promises

"We don't train on your data" and "we don't keep your data" answer different questions:

- **Training:** does your content change the model?
- **Retention:** does a copy of your content sit on the provider's systems, and for how long?

A provider can truthfully promise the first while still doing the second. Ask both questions, separately.

## Where your data can land

Calling a hosted model doesn't change its weights. Your content can still persist in a few places:

- **Abuse-monitoring logs:** prompts and responses, up to 30 days by default at OpenAI [1].
- **Prompt caching:** to speed up repeated requests, parts of a request can be cached briefly on the provider's side, so inference isn't fully stateless [2].
- **Training data:** only if your contract or settings allow it.

## Zero Data Retention (ZDR)

ZDR is a contract arrangement that turns off persistent retention. At OpenAI it has to be approved in advance [1]. Check whether it also covers short-term caching: OpenAI says organizations with ZDR enabled default to keeping the cache in memory only, but some newer models (GPT-5.5 and GPT-5.5 Pro) support only the extended 24-hour retention, so check which option the model you use actually has [2].

## What to ask any model provider

- Do you train on our data by default? Can we opt out in the contract?
- Separately: do you retain prompts and outputs? Where, for how long, for what purpose?
- Is Zero Data Retention available, and how do we qualify?
- Does it cover caching, or only logs?

**Go deeper:** Chapter 5's "Further reading" covers what managed cloud models actually retain. [Read Chapter 5 →](../ch5)
