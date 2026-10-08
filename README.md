# Understanding Modern LLM Systems

### A Field Guide to RAG, Agents, and Beyond

[English](README.md) · [中文](README.zh.md)

A free, book-length guide to how modern LLM systems actually work — RAG, fine-tuning, agents, and where your data goes — written for people who need to understand these systems without reading the papers or writing the code.

**📖 Read it online, free:** [English](https://llmknowledge.pages.dev/) · [中文版](https://llmknowledge.pages.dev/zh/)

---

## Who it's for

- Product managers, solutions and sales engineers, and anyone moving into an AI-adjacent role
- People who review AI projects for security or compliance
- Anyone who keeps hearing "RAG", "agents" and "MCP" in meetings and wants one coherent map instead of scattered fragments

No math or programming background is needed.

## Who it's not for

If you work on LLM training or inference optimization, this will read as introductory. It explains how the systems fit together; it does not teach implementation.

## Contents

| | Chapter |
| --- | --- |
| [Before We Begin](https://llmknowledge.pages.dev/) | What problem is this system solving? |
| [Chapter One · RAG Core Flow](https://llmknowledge.pages.dev/ch1) | The RAG pipeline — how a question becomes a cited answer |
| [Chapter Two · Model Adaptation](https://llmknowledge.pages.dev/ch2) | Adapting a model — fine-tuning vs. RAG, and what each one fixes |
| [Chapter Three · Deep Dive](https://llmknowledge.pages.dev/ch3) | Four core mechanisms — embeddings, retrieval, serving, architecture |
| [Chapter Four · Agents](https://llmknowledge.pages.dev/ch4) | Agents — function calling, MCP, memory, and where they break |
| [Chapter Five · The Compliance Perspective](https://llmknowledge.pages.dev/ch5) | A compliance view — where confidential data actually goes |
| [Chapter Six · The Security Perspective](https://llmknowledge.pages.dev/ch6) | A security view — prompt injection and other risks, from the attacker's side |
| [Chapter Seven · Beyond RAG](https://llmknowledge.pages.dev/ch7) | Beyond RAG — the landscape, organized by what the model is missing |
| [Appendix · Toolkit Overview](https://llmknowledge.pages.dev/appendix) | Toolkit overview |
| [Quick Reference](https://llmknowledge.pages.dev/cheatsheet) | The whole guide on one page |

## What makes it different

- **Built on primary sources.** 49 footnotes point to the original papers and official documentation, so every non-obvious claim can be traced back and checked.
- **7 original diagrams.** Each system is drawn once, clearly, instead of described in paragraphs.
- **One running example.** A single scenario threads through every chapter, so each new concept lands in a context you already know.
- **Two complete editions.** English and Chinese, same content.

## What's new in v2

The biggest addition is a full new chapter: **Chapter Six · The Security Perspective**, which walks through the guide's entire pipeline again — this time from an attacker's point of view. It covers prompt injection, the EchoLeak zero-click exploit that hit Microsoft 365 Copilot (CVE-2025-32711, rated 9.3/10 by Microsoft itself), and a fast-climbing risk category most people haven't heard of yet: attacks that don't breach anything — they just get your system to keep spending money and compute, forever.

The "beyond RAG" chapter (now Chapter Seven) gained a sixth pattern — **reasoning models** — alongside RAG, agents, and fine-tuning, and Chapter Two now also covers reinforcement fine-tuning (RFT), the technique behind how models like DeepSeek-R1 learned to reason.

Under the hood, primary sourcing jumped from 11 to 49 footnotes — vague claims throughout the book got replaced with named papers, CVE records, and vendor documentation (DiskANN's real benchmark numbers, the scaling-law citation behind the "12x model width" rule, actual vector-reversal recovery rates). The 2026 tool landscape in the appendix is refreshed too (Voyage→MongoDB, Jina→Elastic, AutoGen's maintenance mode, and more).

## License

Text and diagrams are licensed under [CC BY-NC-ND 4.0](LICENSE). You're free to read and share it with attribution; commercial use and derivative works are not permitted.

## Support

If this guide helped you, a ⭐ helps other people find it. Corrections are welcome — please open an issue.

A typeset PDF + EPUB edition is available on [Gumroad](https://fallacy04.gumroad.com/l/llm-systems-field-guide).

— koe
