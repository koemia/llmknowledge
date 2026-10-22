---
title: "Can Embeddings Be Reversed Into Text? What the Research Shows"
description: "A 2023 EMNLP study recovered 92% of 32-token inputs word for word from one model's embeddings, and 89% of patient full names. Why vectors aren't anonymous data."
h1: "Can embeddings be reversed back into text?"
chapter: ch5
published: "2026-10-21"
related: [openai-api-data-retention, echoleak-explained]
short: "Yes, to a significant degree, especially for short text. A 2023 study recovered 92% of 32-token inputs word for word from one embedding model, and 89% of patient full names in a clinical test [1]. OWASP recommends treating a leak of vectors alone the same as a plaintext leak [2]. Storing data as vectors does not make it de-identified."
sources:
  - text: "Morris et al., *Text Embeddings Reveal (Almost) As Much As Text*, EMNLP 2023."
    url: "https://arxiv.org/abs/2310.06816"
  - text: "OWASP GenAI Security Project, *OWASP Top 10 for LLM Applications 2026*, LLM09:2026 Vector and Embedding Weaknesses."
    url: "https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/"
---

## What the study found

Morris et al. (EMNLP 2023) reconstructed original text from its embeddings [1]:

- **GTR model, 32-token inputs:** 92% recovered exactly.
- **OpenAI text-embedding-ada-002, 32-token inputs:** 60.9% recovered, falling to 8.0% at 128 tokens.
- **Clinical notes:** 89% of patient full names recovered.

The pattern matters more than any single number: the shorter the text, the more of it comes back. RAG systems split documents into short chunks before embedding them.

## Why "it's just numbers" doesn't protect anything

An embedding's whole job is to keep the meaning of the text: passages that say similar things end up close together, which is how retrieval finds the right one. So think of it less as a scrambled code and more as a detailed summary written in numbers. A summary precise enough to search by can be precise enough to rebuild from, and the shorter the original, the less gets lost.

The OWASP Top 10 for LLM Applications 2026 lists Vector and Embedding Weaknesses as its own entry (LLM09), and recommends treating a leak of vectors alone the same as a plaintext leak [2].

## What to ask or check

- Are our vector stores protected like the source documents: access controls, encryption at rest, customer-managed keys?
- Would we treat a leaked vector database as a data breach? (Assume yes.)
- Are embeddings of sensitive data sent to, or stored by, a third party?

**Go deeper:** Chapter 5 traces where confidential data goes at each stage of a RAG system. [Read Chapter 5 →](../ch5)
