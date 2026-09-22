# Understanding Modern LLM Systems: A Field Guide to RAG, Agents, and Beyond

>
> 

## Before We Begin: What Problem Is This Whole System Actually Solving?

Imagine you're a customer of some software product, asking the company's AI support chatbot on their website: "We're still on the 2023 version — if we upgrade to the new release, will our historical data and custom settings carry over?"

The answer to a question like this is scattered across the company's release notes, migration guides, and support manuals — material a general-purpose large model was never trained on. So in practice, the approach is: **organize and store these documents ahead of time; when a user asks a question, first "look up" the most relevant passages, then hand those passages to the model along with the question, so the model can compose an answer "based on the material."**

This approach — "look up the material first, then have the model answer based on it" — is known in the industry as **RAG (Retrieval-Augmented Generation)**. It's currently the most mainstream, and the easiest starting point for understanding how LLMs get applied in practice, so we'll use it as the throughline for this guide.

This guide starts with the RAG pipeline, works from the surface inward, then expands outward to Agents, compliance, and where RAG sits within the broader landscape of LLM applications.

If you're someone who can't avoid LLMs at work but doesn't need to write code by hand — a product manager, project manager, pre-sales or solutions engineer, founder, or a manager who needs to work with AI projects — what you need usually isn't runnable code, but the kind of understanding that lets you talk with engineering teams, evaluate approaches, and explain things clearly to clients. This guide is written for exactly that: by the end, you should be able to follow how a real LLM system actually works, keep up with the relevant technical discussions, and judge whether RAG or some other approach fits a given need.

If you're just starting out technically, it will help you first build a complete conceptual map, so that later, when you read framework documentation or start writing code, you won't be stuck seeing the trees but missing the forest.

No math or programming background is needed anywhere in this guide. The content moves from simple to deep: the early chapters start with everyday examples, and later chapters move closer to how the system actually works internally under the hood. You can read straight through, or just take the parts you need.

---

## Chapter One · RAG Core Flow: How a Question Becomes a Cited Answer

Eight steps — you can think of the whole process as "a secretariat preparing a briefing response for an executive":

| Step | What the System Does | Everyday Analogy |
|---|---|---|
| ❶ Receive the question | The system receives the question the user typed in | The executive assigns a task: "Find out about X for me and give me a written response" |
| ❷ Embed & understand | First "clean up" the question to make it easier to search — rewriting vague phrasing, adding synonymous ways of saying it, breaking a complex question into several smaller ones — then convert it into a string of numbers (a vector), so the computer can "understand the meaning" and compare it against the database | The secretary first makes sure they understand the assigned question clearly — clarifying anything vague, rephrasing it into the standard terms used in the filing system — before they can go pull the right files |
| ❸ Retrieve | Take that string of numbers and search the database for the most relevant passages. In a real system, this step is a "wide-to-narrow funnel": first search two channels at once (meaning-based vector search + literal keyword search), then filter out anything that shouldn't appear (like content you don't have permission to see, or content that's outdated), and finally use a more careful model to re-rank the remaining candidates (called "reranking"), keeping only the most relevant passages | The secretary goes to the archive room to pull files: searching several channels at once, excluding classified files they aren't cleared to see and superseded old versions, then reading each remaining document closely and keeping only the pages that actually answer the question |
| ❹ Augment (assemble prompt) | Assemble "the retrieved material" + "your original question" + "the system's behavior instructions" into one complete piece of text, ready to hand to the model. The name "Augmented" comes from RAG's full name, Retrieval-**Augmented** Generation — using the retrieved material to augment your original question is exactly what this step does | The secretary puts the retrieved documents, the executive's original question, and the instruction "write from the material, don't improvise" all into one working folder |
| ❺ Generate | The large language model reads this folder and writes out the answer word by word | The department's designated writer takes the folder and drafts the response based on the material inside |
| ❻ Guardrails | The system checks whether the answer has any problems (like leaking something it shouldn't, wrong formatting, or obvious fabrication) — this check mechanism is standardly called "Guardrails" in the industry. More sophisticated systems also have the model "check the answer against the retrieved material again itself," and revise if it finds a discrepancy (this self-check step is called reflection) | The drafter first checks their own draft against the original documents, then the department head reviews and signs off before it can be submitted upward |
| ❼ Respond with citations | Return the answer to you along with a citation of "which document and which passage this statement is based on" | The response submitted to the executive notes "based on Article X of Document Y," so the executive can pull the original document to verify at any time |
| ❽ Log | The system records this round of Q&A — usually keeping two copies: a **log** (a persistent record for later troubleshooting, auditing, and statistics) and **conversation history** (kept as context for your next question — the two records serve different purposes and are often stored in different places) | The office logs it for the record: who assigned it, when it was handled, which files were pulled, and what the response was — and at the same time files this exchange into that executive's correspondence folder, so it can easily be referenced the next time they assign something |

<figure>
<img src="images/rag-8-steps.svg" alt="Diagram of the RAG eight-step pipeline: Receive Question → Embed & Understand → Retrieve → Augment (Assemble Prompt) → Generate → Guardrails → Respond with Citations → Log">
<figcaption>Figure 1: The RAG eight-step pipeline</figcaption>
</figure>

**A note: what people usually call "RAG" is really just the middle section of this table.** The RAG defined in papers and tutorials is, at its core, just three steps: ❸ Retrieve → ❹ Augment → ❺ Generate — which happen to match the three words in RAG's full name (Retrieval, Augmented, Generation); ❷ converting to a vector is a prerequisite for retrieval, so it's generally counted in too. The remaining steps aren't part of RAG itself: ❶ and ❼ are the "receive-and-respond" that any online service has, ❽ is operational record-keeping, and ❻ is a hardening measure for production systems. So when someone says "we've built RAG," they usually mean just that middle section; this table describes the complete pipeline you get once you put RAG into a real production system and run it.

**Which "department" handles each of these eight steps**:

| Department | Steps It Handles | What It Is |
|---|---|---|
| Frontend | ❶ Receives your question, ❼ presents the response to you | The chat window where you type your question and see the answer |
| Orchestration / Backend | Directs the order and gating of all eight steps; personally handles ❹ assembly and the rule-checking in ❻ | An invisible coordinating program — it doesn't "answer the question" itself, but decides where to get material from, how to assemble it, and whether to hold the output for review after generation. Chapter Three will expand on an important rule: it's the only "active initiator" in the entire system |
| Model | ❷ Converts text into vectors (embedding service), ❺ generates the answer (LLM service) | The AI that actually does "understanding meaning" and "writing the answer." Both services can be deployed in two forms: **cloud-hosted** (i.e., MaaS, Model-as-a-Service — the model runs on the provider's cloud and is called over the network, so you don't need to buy your own hardware) or **self-hosted** (you run it on your own machines, so data never leaves your company's boundary). Which form to choose is a key decision covered in the compliance discussion in Chapter Five |
| Data | ❸ The place retrieval searches | **Vector database** (stores the vectors converted from the material, and usually also a plaintext copy of the original — once you find the vector, you can pull up the original text) + **document / object storage** (where the original PDF, Word files themselves are kept) |
| Support | ❽ Where the "log" copy of the record goes (the other copy, "conversation history," is kept by the backend for the next round) | Logging / observability systems — every "who asked what, what was retrieved, what was answered" gets a persistent copy for troubleshooting and auditing. Chapter Five covers this: it's the corner of compliance most easily overlooked |

<figure>
<img src="images/dpt-4-steps.svg" alt="Diagram of which department handles each of the eight steps: Frontend handles ❶ receiving the question and ❼ presenting the answer, Orchestration/Backend directs the whole pipeline and personally handles ❹ assembly and ❻ rule-checking while also initiating ❸ retrieval matching, Model handles ❷ vectorization and ❺ AI generation, Data is where the ❸ retrieval knowledge base lives, Support keeps the ❽ operational logs, and conversation history is kept by the backend">
<figcaption>Figure 2: Which department handles each of the eight steps</figcaption>
</figure>

### Offline Indexing: The Everyday Prep Work Outside the Eight Steps — Where Does the Material Retrieval Searches Come From?

The eight steps above all describe what happens "after the executive assigns the task" — but one precondition got skipped: who put the vectors into that vector database that ❸ retrieval searches, and when? The answer is a separate preparation pipeline that runs continuously outside the eight steps, called **offline indexing** ("offline" meaning: it doesn't happen live while answering a question, but is done ahead of time):

Document → Parsing (reading formats like PDF and Word into plain text) → Chunking (cutting long documents into segments, say a few hundred characters each, because the model can't read too much at once and precise retrieval gets harder with long chunks) → Embedding (converting each small chunk into a numeric vector) → Storing it in the vector database.

<figure>
<img src="images/offline-indexing.svg" alt="Offline indexing pipeline diagram: raw documents go through document parsing, text chunking, and text embedding, then the vectors are stored into the vector database">
<figcaption>Figure 3: The offline indexing pipeline — from raw documents to the vector database</figcaption>
</figure>

This step is like the archive room **routinely** filing, cataloging, and organizing all documents by topic ahead of time, so they can be pulled on demand later — without doing this first, every time the executive assigns a task, you'd have to re-search the entire company's documents from scratch on the spot, which would be unbearably slow. It's also not a "do it once and done" job: new and revised documents, or adjustments to retrieval strategy, all trigger index updates or rebuilds — Loop D below covers what drives this.

### Are These Eight Steps a Straight Line? Four Loops

Looking at a single smooth Q&A exchange, the eight steps really are a straight line from start to finish (the output of one step is the raw material for the next, and the order can't be scrambled). But a real system hangs a few "loop-backs" off this main trunk, which kick in and send things back under certain conditions:

- **Loop A · Search Again**: Before generating an answer, the model discovers "the retrieved material isn't enough to answer this question," so it rephrases and goes back to ❷❸ to retrieve another round — possibly repeating several times until the material is sufficient. **The key point: how many rounds it searches isn't hard-coded in advance — the model decides on the spot** — this is exactly the "agentic" way of working that Chapter Four covers later.
- **Loop B · Guardrail Rejection**: When the ❻ check fails, the system falls back to ❺ to regenerate, or back to ❸ to re-retrieve, according to pre-defined rules. Unlike Loop A, here "under what conditions to fall back, to where, and how many times at most" are all rules engineers hard-coded in advance — the model has no say in the decision.
- **Loop C · Multi-Turn Conversation**: The model itself has no memory — once a round of Q&A ends, it "remembers" nothing. The reason you can follow up with "what about the second one" is that ❽ saves the question and answer into **conversation history** every round (note: this is the "conversation history" copy of the two records ❽ keeps, not the log); when you send a new question, the working folder ❹ assembles includes this history alongside the new question and newly retrieved material, and the model rereads all of it on the spot to figure out what "the second one" refers to. This loop in one sentence: **the previous round's output becomes part of the next round's input**.
- **Loop D · Logs Feeding Back**: The logs ❽ accumulates are periodically handed to an evaluation system for analysis (which kinds of questions get answered poorly, and whether it was retrieval or generation that got it wrong); engineers use the findings to adjust chunking methods and retrieval strategy, then rebuild the offline index. This loop cycles on a scale of days or weeks, and the decisions in this loop are made by people, not the system.

<figure>
<img src="images/rag-loop-a.svg" alt="Diagram of Loop A: the model finds the material insufficient and falls back from ❺ Generate to ❷ Embedding to retrieve another round; only ❷❸❺ are shown in color, other steps are grayed out">
<figcaption>Figure 4: Loop A · Search Again</figcaption>
</figure>

<figure>
<img src="images/rag-loop-b.svg" alt="Diagram of Loop B: when the ❻ rule check fails, the system falls back to ❺ to regenerate or to ❸ to re-retrieve per preset rules; only ❸❺❻ are shown in color, other steps are grayed out">
<figcaption>Figure 5: Loop B · Guardrail Rejection</figcaption>
</figure>

<figure>
<img src="images/rag-loop-c.svg" alt="Diagram of Loop C: conversation history is appended into the ❹ material-assembly folder in the next round; only conversation history and ❹ are shown in color, other steps are grayed out">
<figcaption>Figure 6: Loop C · Multi-Turn Conversation</figcaption>
</figure>

<figure>
<img src="images/rag-loop-d.svg" alt="Diagram of Loop D: ❽ operational logs, after human evaluation, feed back into rebuilding the knowledge base index; only ❽ and the knowledge base are shown in color, other steps are grayed out">
<figcaption>Figure 7: Loop D · Logs Feeding Back</figcaption>
</figure>

### Further Reading: RAG's "Generational" Classification

RAG has kept evolving since it first appeared, and the industry conventionally divides it into three generations.

The first generation is called **Naive RAG**: the eight steps run straight through, and each step does only the simplest possible version. The second generation is called **Advanced RAG**[^rag-survey]: the skeleton stays the same, but every step gets more refined — ❷ adds rewriting and decomposition, ❸ becomes the wide-to-narrow funnel, ❻ adds reflection and correction, plus rule-triggered retries like Loop B. The "real system" described in this chapter belongs to this generation. The third generation is called **Agentic RAG**[^agentic-rag], which Chapter Four covers in depth.

The dividing line between the three generations isn't whether loops exist, but **who decides the loop**. In the first two generations, the looping rules are written into the code in advance by engineers, and the system just executes them; Agentic RAG instead hands "whether to search again, and how" to the model to judge on the fly — Loop A is exactly this case. As for Loops B, C, and D, in the first two generations their decision-making power likewise stays with rules and people: B is triggered by preset rules (the rules can ask the model to act as a "scorer" internally — for instance, having the model rate the quality of retrieved results — but which path to take after scoring is still decided by the rules), C attaches history in a fixed way, and D is driven by engineers — so their presence doesn't change the generational classification. Conversely, the moment a loop's decision-making is genuinely handed over to the model — for example, having the model judge for itself whether the answer is well-grounded and whether to re-retrieve or rewrite (the industry does have approaches like this, such as Self-RAG[^selfrag]) — by the same standard, that loop becomes agentic too. In short: the three generations use the same components; what changes is who's in command.

[^rag-survey]: Gao et al., *Retrieval-Augmented Generation for Large Language Models: A Survey*, 2023 — the earliest source for the "Naive RAG / Advanced RAG / Modular RAG" three-generation classification. The original paper calls the third generation "Modular RAG"; this section swaps in the more fitting and more commonly used term "Agentic RAG," sourced in the next footnote. https://arxiv.org/abs/2312.10997

[^agentic-rag]: Singh et al., *Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG*, 2025. https://arxiv.org/abs/2501.09136

[^selfrag]: Asai et al., *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection*, ICLR 2024 (oral, top 1% of submissions). https://arxiv.org/abs/2310.11511

---

## Chapter Two · Model Adaptation: Turning a General Model into a Usable System

After the AI customer support bot went live, the team received three distinct kinds of complaints.

**The first kind: it can't answer.** A customer asked what changed in the new release published last week, and the bot said it didn't know — the release notes hadn't been added to the knowledge base yet.

**The second kind: the answer is correct, but unreadable.** The content was accurate, but a wall of text with no bullet points, no source citations, and a tone that drifted unpredictably. The team wanted it to always lead with a conclusion, then list steps, and append document links at the end.

**The third kind: fluent prose, completely beside the point.** A semiconductor customer asked a question loaded with industry jargon, and the bot answered eloquently — about the entirely wrong thing. It fundamentally didn't understand what those terms mean in that industry.

All three sound like "the AI isn't working," but the root causes are entirely different: the first is a **knowledge gap**, the second is a **behavior gap**, the third is a **comprehension gap**. Any general-purpose model deployed for a specific use case will show cracks at these three seams; the work of closing those gaps and turning a general-purpose base model into a system that's genuinely usable for a given scenario is called **model adaptation**.

### Only Two Intervention Points: the Input, or the Weights

Three kinds of gaps, three kinds of solutions. The simplest way to tell them apart is to ask: what does the solution actually change — does it leave the model untouched and only change what's placed in front of it each time, or does it go in and alter the model itself?

One approach intervenes on the **input**: the model's parameters stay completely unchanged; you just feed in the right material with each question. The RAG from Chapter One is this type.

The other approach intervenes on the **weights**: it directly modifies the model's internal parameters. Parameters (also called weights) are the enormous collection of numbers inside the model — often billions or hundreds of billions of them — in which all of the model's abilities are stored: which words it recognizes, how it habitually phrases things, how it decides what word to write next given the preceding text. "Training" is the process of iteratively adjusting these numbers. Once this kind of change is done, it's baked into the model, and every subsequent answer carries it. **Fine-tuning** and **continued pretraining** fall into this category.

### Three Approaches, Each in Its Place

| Approach | Which Gap It Fixes | Intervention Point | Update & Cost |
|---|---|---|---|
| **RAG (Retrieval-Augmented Generation)** | **Knowledge gap**: material the model has never seen — company documents, recent changes | Input | Swap in a new document and it takes effect immediately; the cost is in per-query retrieval and longer prompts |
| **Fine-tuning / SFT** (Supervised Fine-Tuning) | **Behavior gap**: format, tone, and behavior don't meet requirements — e.g., enforcing a fixed conclusion-then-steps structure, standardized citation formatting | Weights | Requires preparing a batch of "question + reference answer" examples and running training; to change it, you have to retrain |
| **Continued pretraining** | **Comprehension gap**: the domain language itself is beyond the model's understanding — heavy code, specialized legal corpora, technical text in low-resource languages | Weights | Requires massive domain-specific text and large-scale compute; usually only large organizations do this |

> **Note: what does "retrain" mean?** It means running the training process again — preparing a fresh batch of example data, having the model learn on that data for another round, and producing a new version of the weights (or a new version of the adapter). It's not something you can do as casually as changing a line of configuration, but it's also not as out of reach as many people imagine.
>
> **When it comes to fine-tuning, the compute barrier fell long ago.** Thanks to techniques like LoRA that train only a small fraction of the parameters, fine-tuning a 7–8B model in 2026 costs roughly a few dollars to low tens of dollars in GPU rental, taking two to four hours; using a managed service with pay-per-use pricing, a typical job runs to a few tens of dollars.[^lora-cost][^lora-cost-more]
>
> **The real effort is before and after training.** The industry consensus is: GPUs are no longer the main expense — data preparation and evaluation are. Taking a fine-tuning project from start to finish (curating examples, cleaning and labeling data, iterating on experiments, building an evaluation set) typically lands in the range of a few thousand to tens of thousands of dollars, most of which goes to people and data, not compute. So the burden of "to change it you have to retrain" is mainly not about how expensive a single training run is, but that every change means redoing the entire preparation-and-validation cycle.
>
> **Continued pretraining is an entirely different order of magnitude**: it consumes massive domain corpora and large-scale compute, and typically requires a dedicated team and infrastructure.

**Using the wrong tool is a common trap, and the most typical version is: wanting the model to learn new facts, so you fine-tune it.** Research has repeatedly shown that models struggle to learn new factual knowledge through fine-tuning — training examples that introduce new knowledge are learned noticeably more slowly than others; and by the time this new knowledge is finally absorbed, the model's tendency to fabricate content actually increases.[^gekhman] The conclusion: factual knowledge is primarily acquired during pretraining; what fine-tuning teaches the model is to more effectively deploy the knowledge it already has. So when the model can't answer something (the first kind of complaint at the start of this chapter), the right fix is to retrieve the material and put it in front of the model, not to bake the material into the weights.

The reverse is equally true: RAG will not change the model's behavior, tone, or output format. If the model is verbose, RAG can't fix it; if the format is wrong, RAG can't fix it either. The second kind of complaint can only be addressed through fine-tuning.

### In Practice, They're Usually Stacked

These three approaches aren't pick-one. A common combination in production systems is: use an adapter (a lightweight fine-tuning add-on module that doesn't modify the entire model but hangs a small block of new parameters alongside it — the representative technique is LoRA) to handle tone and citation formatting, while RAG manages knowledge — the adapter gets updated once a quarter, the knowledge base is updated continuously. The principle can be summed up in one sentence: **language through training, facts through retrieval; anything that changes should not be baked into the weights.**

The order of operations matters too. The lowest-cost approach is to adjust the prompt; next comes RAG; fine-tuning only comes after that. The prevailing industry advice is: before deciding to fine-tune, make sure you already have an evaluation set, and that the "prompt + RAG" approach genuinely failed to pass it — otherwise you'll likely spend the money on training without actually solving the real problem.

Regardless of which path you take, the endpoint is the same place: the model's weights (the base model, plus any stacked adapter) → the inference service (the process where the model actually "runs" and generates an answer) → the answer. The next chapter covers how this machinery actually works.

[^lora-cost]: Stratagem Systems, *LoRA Fine-Tuning Cost in 2026: Real GPU Prices, QLoRA Math & Free Calculator*, pricing verified July 2026. https://www.stratagem-systems.com/blog/lora-fine-tuning-cost-analysis-2026

[^lora-cost-more]: Specific prices vary with hardware and provider; the figures here are meant only to indicate the order of magnitude. Numbers in the same range can be found in [io.net, *LLM Fine-Tuning Budget Guide: GPU Costs, Timelines, and What to Spend*](https://io.net/blog/llm-fine-tuning-budget-guide-gpu-costs-timelines-and-what-to-spend) and [Awesome Agents' fine-tuning cost comparison](https://awesomeagents.ai/pricing/fine-tuning-costs-comparison/), but all specific numbers cited in this section come from the Stratagem article cited above.

[^gekhman]: Gekhman et al., *Does Fine-Tuning LLMs on New Knowledge Encourage Hallucinations?*, EMNLP 2024. https://arxiv.org/abs/2405.05904

---

## Chapter Three · Deep Dive: Four Core Technical Mechanisms

### 3.1 Embedding: How Machines "Understand" the Meaning of Language

**First, why it's needed**: at bottom, computers can only do math with numbers — they don't understand the relationship between the words "cat" and "dog." But if we can turn every word and every sentence into a string of numbers (say, a "coordinate" made up of 1,024 numbers), and arrange things so that "phrases with similar meaning" end up "close together" in the space these numbers represent while "phrases with unrelated meaning" end up far apart, then the computer can indirectly judge whether "these two sentences are about the same thing" simply by **calculating the distance between two coordinates**. This string of numbers is called an "embedding vector," and the conversion process is called "embedding."

**An analogy**: imagine a vast library where the librarian doesn't shelve books alphabetically, but instead **places books on similar topics on neighboring shelves** — a book about cats and a book about dogs both belong to the "pets" category, so they'd be placed close together; a book about cats and a book about auto repair would be placed far apart. To find "books similar to this one," you just look at what's sitting next to it. Embedding does exactly this, except instead of placing books on three-dimensional shelves, it places them in an abstract space with hundreds or thousands of dimensions (the human brain can't directly visualize what "1,024-dimensional space" looks like, but mathematically it's perfectly computable).

**How this string of numbers is "learned"**: nobody manually decrees that "cat = [0.2, 0.8, ...]." Instead, it's done through a training method called **contrastive learning** — the model is shown vast quantities of "these two sentences are related" and "these two sentences are unrelated" examples, and every time it gets one wrong, its parameters are nudged slightly, pulling "related" pairs closer in the space and pushing "unrelated" pairs further apart. After repeating this millions of times, the model organically "figures out" a coordinate system in which "close together = similar in meaning" holds true. **No single dimension is deliberately designed to "represent a specific meaning"** — meaning is distributed across the combined "position" formed by all dimensions together, much like a person's character isn't determined by any single trait but by the overall impression composed of many traits.

**The technical process in concrete terms (two steps)**:

1. **Tokenization**: first, the text is cut into small units the model can process, called "tokens." Note that a token is neither a "word" nor a "character" — it's a **segment divided by frequency of occurrence**: common algorithms (BPE, SentencePiece) start by splitting text into its smallest units, then repeatedly merge the pair that "appears together most frequently," until a vocabulary of the desired size is reached (typically 50,000 to 150,000 entries). So high-frequency words may be a single token, while rare words get split into several subword pieces.

   This design has a practical benefit: no matter how rare or newly coined a word is, it can always be decomposed into known subwords or even individual bytes — there's never a situation where "this word is unrecognized and can't be processed." That was a common failure point with earlier tokenization methods.

   One more point that's practically relevant to cost: **the same passage of text takes up very different numbers of tokens in different languages.** English runs roughly 4 characters per token; Chinese typically uses one to two characters per token. Since both model pricing and "how much it can process at once" are measured in tokens rather than characters, the same volume of Chinese content often consumes more tokens than its English equivalent.

2. **Encoding (Transformer neural network)**: the sequence of tokens is fed into a neural network called a "transformer," which computes a vector for each token, then combines them via "pooling" (merging many token vectors into a single vector representing the whole sentence) and "normalization" (scaling the vector to unit length, so similarity can be compared using a standardized method). The result is a single vector that represents the meaning of the entire sentence. How many numbers this vector contains (i.e., its "dimensionality") — in 2026 the common range is 384 to 4,096, with general-purpose scenarios typically starting at 768 or 1,024, then adjusting based on retrieval quality and storage cost.

> **A note**: earlier embedding models mostly used "encoder" architectures like BERT, while the current top-performing batch (e.g., NV-Embed, E5-mistral, GritLM) instead start from a large language model and add a pooling layer plus contrastive fine-tuning on top. Both approaches produce sentence vectors, and the usage is exactly the same — readers don't need to dig into the difference.

**One limitation you must know about: embedding models have a maximum input length per call.** Every embedding model specifies a maximum number of tokens for a single input; anything beyond that limit is silently truncated — with no error or warning. A chunk that's too large may have its second half simply not represented in the vector, making it permanently invisible to retrieval. This is one of the hard reasons why the "offline indexing" step in Chapter One must chunk long documents first: chunk sizes must fall within the length limit of the embedding model being used.

**A rule that's easy to trip on but critically important**: when you convert documents from your knowledge base into vectors ahead of time (this is called "indexing"), and when you convert the user's question into a vector at query time (this is called "querying"), **you must use the same embedding model for both**. The reason is simple: different models "learn" different coordinate systems, just like two maps that use different scales and different origin points — you can't take coordinates from Map A and look them up on Map B. So if you want to switch to a different embedding model, you can't just swap out the query side — **you have to recompute every vector in the entire database (called re-embedding)**, and the dimensionality of the stored vectors and the query vectors must match.

The "dimensionality must match" above means the vectors stored in the database and the vectors computed at query time must be the same length — otherwise they simply can't be compared. But this doesn't mean the dimensionality itself is permanently fixed. Current mainstream models widely support a technique called **Matryoshka (nesting-doll) embeddings**: a long vector computed by the same model can simply have its trailing dimensions chopped off without retraining — for example, keeping only the first 256 out of 1,024 dimensions typically degrades retrieval quality by only a few percentage points, while dramatically reducing storage and search costs. If you want to save costs this way, that's perfectly fine — just make sure both the stored vectors and the query vectors are truncated to the same length.

### 3.2 Retrieval: How to Find Everything That Should Be Found

Chapter One mentioned that retrieval in a real system is a "wide-to-narrow funnel." This section explains why the funnel is designed this way — what deficiency each layer compensates for in the layer above it.

**Start with the base capability: what vector search can do**

Section 3.1 explained that text with similar meaning produces vectors that are close together. So the most basic form of "retrieval" is: convert the question into a vector too, then find the entries in the database whose positions are closest. As for how "closest" is concretely calculated, in practice it usually yields a score between 0 and 1, where closer to 1 means more closely matched in meaning — the "score 0.82" you see in the system is this number. Under the hood it's computing the angle between two vectors: the more aligned the directions, the higher the score. No need to dig into the details.

The greatest strength of this approach is that **it doesn't depend on literal wording**. A user asks "how do I move old data to the new version"; the documentation says "historical record migration procedure." The two sentences share not a single word in common, yet vector search connects them anyway. This is its fundamental advantage over traditional keyword search.

**First-layer deficiency: at scale, comparing every single entry is unacceptably slow**

If the database holds ten million vectors, comparing against every one of them and sorting the results for each question is something real-time Q&A simply can't sustain. The solution is **ANN (Approximate Nearest Neighbor)**: rather than insisting on finding the absolute most similar entries with 100% accuracy, ANN uses pre-built index structures to compare against only a small fraction, trading a tiny loss in precision for a speedup of several hundred times.

This "precision" has a standard measure, called **recall@k (top-k recall)**: out of the truly most similar top k entries, how many were actually found and returned. It's an adjustable knob, not a fixed setting — and the cost curve gets steep the higher you push it: going from 0.8 to 0.95 increases latency by roughly 30%, which is tolerable; pushing from 0.95 toward 0.99 can increase latency three- to fivefold. Most production systems settle around 0.95.

The specific index structures come in three main types, and which one to use depends on data scale:

- **HNSW** (Hierarchical Navigable Small World graph): pre-connects all vectors into a "neighbor relationship graph"; at query time, it works like playing "six degrees of separation" — starting from one point, at each hop jumping to a neighbor closer to the target, reaching the target region in just a few steps. **The default choice for most production systems in 2026** — high recall, supports adding new data at any time. Its one hard constraint is that the entire graph must fit in memory, so the practical single-machine limit is roughly 100 to 200 million vectors.
- **IVF** (Inverted File Index): uses k-means to roughly cluster all vectors into groups, then at query time only searches the most relevant few clusters in detail. Lower memory usage than HNSW, but also lower recall under equivalent conditions — suited for large datasets with mostly static content and tight memory budgets.
- **DiskANN**: keeps the full index on SSD, with only compressed vectors and navigation structures in memory. The standard answer at the billion-vector scale — a single node can handle one billion vectors, 95% recall, 5ms latency, with memory usage roughly 90% lower than pure in-memory approaches.

Implementations of these methods can be found in FAISS (an open-source vector search library) and various commercial vector databases.

**Second-layer deficiency: vector search misses things that require exact literal matches**

Vectors' strength is understanding semantics, and that's also their weakness — they're **insensitive to literal text**. A user asks "does model X-200 support this feature?"; vector search is likely to return a bunch of passages about product specifications in general, yet miss the specific line that actually mentions X-200. Product model numbers, error codes, personal names, legal article numbers, version numbers — for content where a single character difference means something entirely different, semantic similarity is virtually powerless.

So production systems typically **run two retrieval tracks in parallel**: vector search for "meaning matches" and keyword search (the industry-standard algorithm is called BM25) for "literal matches," then merge the two result sets. This is **hybrid search**, and what Chapter One called "searching through two channels at once." When merging, because the two scoring systems aren't on the same scale, a conversion rule is needed. The common approach is called **RRF (Reciprocal Rank Fusion)** — rather than comparing scores directly, it only looks at what rank each result occupies in its respective list, and entries that rank highly in both get a higher combined score.

**Third-layer deficiency: some of what's retrieved, the user shouldn't be allowed to see**

Feeding retrieval results directly into the prompt is dangerous: different users have access to different documents; a customer shouldn't see internal-version documentation, and an external partner shouldn't see internal pricing details. So at the time of chunking and indexing, every chunk must carry metadata about which document it came from and who is allowed to see that document (i.e., ACL — Access Control List), and retrieval must filter in real time based on the querying user's identity. The same applies to timeliness filtering — superseded old-version documents shouldn't be dug up and used as evidence.

This step is more engineering-intensive than it sounds: **filter first, then search** breaks the ANN index structure (the neighbor-relationship graph was built on the full dataset — remove some of the points and the paths break); **search first, then filter** risks retrieving 50 entries but being left with only 2, or even zero, after filtering. Mature vector databases provide specialized filtered-search mechanisms for this, but it remains one of the most frequent sources of performance issues in real deployments.

**Fourth layer: the dozens of rough-screened results still need further selection**

The goal of the preceding layers is "**don't miss anything**" — better to bring back too many than too few. But the material stuffed into the prompt can't be too much: there are length limits, and irrelevant content distracts the model's judgment. So a final round of **reranking** is needed: a more precise but slower model takes the few dozen rough-screened results, compares each one against the question individually, rescores and reorders them, and keeps only the most on-point handful.

A reranking model works differently from an embedding model: the embedding model converts the question and the document **separately** into vectors and then compares distances — fast but coarse; the reranking model reads the question and the document **together** in one pass and then scores — slow but much more accurate. Precisely because it's slow, it can only be used after the candidate set has been narrowed to a few dozen — which also explains why the entire funnel has to be "wide first, then narrow": use fast-and-coarse methods to shrink the scope from millions to dozens, then use slow-and-precise methods to pick a handful out of those dozens.

### 3.3 LLM Serving: How the Model Handles Many Users at Once

The previous two sections covered "how the material gets found." This section covers what happens after the material is handed to the model. Note the keyword here is **serving** — the focus isn't only on how the model computes internally, but on how a server organizes things when it needs to serve hundreds or thousands of users simultaneously.

**A single inference happens in two phases**

The way a model generates text is called **autoregressive generation**: it produces one token at a time, appends it to the existing text, then predicts the next token based on "everything so far," repeating until it produces a stop token.

This creates two phases with opposite computational characteristics:

- **Prefill**: reads the entire input (system instructions + retrieved material + user question) **all at once in parallel**, computing two things (K and V, explained below) for every token, and storing them in a GPU memory buffer called the **KV cache**. This phase is compute-bound.
- **Decode**: starting from the first output token, generates **one at a time, sequentially**. Each new token written requires looking back at all preceding content. This phase is memory-bandwidth-bound — the bottleneck isn't how fast you can compute, but how fast you can read the KV cache into the processor.

**Why the KV cache must exist**: decode requires looking back at all preceding text for every new token. If every token required recomputing all the preceding tokens from scratch, then by the 100th token you'd be recomputing the first 99 — this redundant computation grows quadratically with text length, making long outputs completely impractical. Storing and reusing previously computed results brings the computation down to near-linear. **Trading GPU memory for eliminated redundant computation** — that's the entire point of the KV cache.

So what are K and V? When the model processes each token, it computes three vectors: **Q** (the question this token carries: "which preceding tokens are relevant to me?"), **K** (the sign each token holds up, reading "here's what I'm about"), and **V** (the actual information this token carries). The current token takes its Q and compares it against the K of every preceding token; whichever matches most strongly gets a higher weight; then the V values from all tokens are combined via weighted average — this is "attention." The reason only K and V are cached, not Q, is that K and V get reused by every subsequent new token — worth storing; Q is only used once in the current step, then discarded.

**Two metrics for measuring speed**

These two phases each correspond to a standard industry metric; understanding them lets you follow most discussions about inference performance:

- **TTFT** (Time To First Token): the time from sending the request to seeing the first output token, determined by prefill.
- **TPOT / ITL** (Time Per Output Token / Inter-Token Latency): after output begins, the rhythm between successive tokens, determined by decode.

It's worth noting that **total wait time is usually dominated by decode**. A response of roughly 500 tokens, at 80 milliseconds per token, takes about 40 seconds for decode alone; by comparison, the time to first token might be only 200 milliseconds. So "the longer the answer, the slower it feels" is a linear accumulation — the user experience is very direct.

**How a server handles many users at once: continuous batching**

If a server processes one request at a time, finishing it before accepting the next, the GPU sits idle most of the time — because during decode, compute capacity goes underutilized, resulting in severe waste.

Modern inference frameworks (vLLM, SGLang, etc.) use an approach called **continuous batching**: in each iteration, all currently active requests **each advance by one token**, then the next iteration begins; when a request finishes it exits the batch, and when a new request arrives it joins immediately — no need to wait for the entire batch to complete. This is the key to keeping the GPU fully utilized, and the reason it can serve dozens to hundreds of users simultaneously.

This mechanism also explains a phenomenon everyone has encountered: **the response stutters for several hundred milliseconds mid-stream**. When a new request's prefill squeezes into the batch, it demands a large burst of compute, forcing the requests currently outputting token-by-token to wait — what the user sees is the text stream suddenly freezing.

**A few practical cost rules**

- **Longer inputs make prefill costs rise faster than you'd expect.** The computational complexity of attention is quadratic in input length, so doubling the reference material from 2,000 to 4,000 tokens doesn't just double this component of the cost — it roughly quadruples it. This is the hidden price of "stuff more material into the prompt."
- **Longer answers increase decode time linearly**, and decode usually dominates the user's total wait time.
- **The KV cache is a significant consumer of GPU memory**, and it grows as the context gets longer — it's the main constraint on how many users a single machine can serve concurrently. To address this, the industry developed optimizations like **PagedAttention**[^pagedattention]: managing KV cache the way an operating system manages memory pages, preventing large blocks of GPU memory from sitting idle. The open-source inference framework vLLM uses exactly this approach.

**An important optimization for prefill: prompt caching.** In a RAG system, the beginning of every request is often identical — the same system instructions, sometimes the same long document. Since the content is the same, the computed KV cache is also the same, so there's no need to recompute it every time. Cloud providers therefore widely offer cross-request prefix caching: the KV cache for this shared prefix is retained for a period (typically minutes to hours), and subsequent requests that hit the same prefix reuse it directly, saving precisely that quadratic prefill cost.

This mechanism has an easily overlooked implication: the KV cache is not, as commonly assumed, "computed and discarded, existing only within the current request." With caching enabled, a portion of the content resides briefly in the provider's infrastructure — Chapter Five will return to this point when discussing compliance.

### 3.4 Who Calls Whom: How the System's Components Divide the Work in a Single Query

**The core rule**: across the entire system, **only the "backend / orchestration layer" actively initiates actions**. The vector database, the model services — these components are all passive: they respond only when asked, and they **never communicate directly with each other**.

Using the secretariat analogy from Chapter One, the backend is the secretary who owns this task. Which archive room to pull files from, what to do if they can't be found, whether the material is sufficient, whether to go back for another round, whether the draft is fit for submission — every one of these decisions is made by the secretary, and if something goes wrong, the secretary bears responsibility. The archive room's only job is "when someone comes to pull files, hand them over"; the writer's only job is "when material arrives, draft a response." The two never deal with each other directly — they may not even know the other exists. So the backend is not a messenger; it's the sole owner of this task.

**The complete communication sequence**:

1. **Frontend → Backend** (corresponds to Chapter One ❶ Receive the question): the user's question is sent to the backend.
2. **Backend → Embedding service** (corresponds to ❷ Embed & understand): sends the question text over, requesting it be converted into a query vector.
3. **Backend → Vector database** (corresponds to the first half of ❸ Retrieve): performs a similarity search using the query vector, simultaneously applying permission filtering based on the querying user's identity (ACL — Access Control List), and retrieves the most relevant entries (called top-k). The keyword search described in 3.2 is typically completed in this same step — most vector databases have this capability built in, returning both retrieval tracks' results merged in a single call. Only when the keyword index is a separate standalone system (e.g., a separately deployed Elasticsearch) does this step become two calls, with the backend merging the two result sets.
4. **Backend → Reranking service** (corresponds to the second half of ❸ Retrieve): sends the few dozen rough-screened results along with the question, requesting the service to score and reorder each one, keeping only the most relevant handful. The reranking model is the same type of component as the embedding model — both are standalone model services running on GPUs, which can be self-hosted or called via a ready-made API.
5. **Backend (completed internally, no external call)** (corresponds to ❹ Augment): assembles the system instructions, retrieved original text, conversation history, and user question into the complete prompt.
6. **Backend → Generation model service** (corresponds to ❺ Generate): sends the complete prompt over, requesting it to generate an answer.
7. **Backend → Frontend** (corresponds to ❻ Guardrails and ❼ Respond with citations): receives the model's output stream while checking it; the portions that pass are pushed to the interface along with their source citations.
8. **Backend → Logging system** (corresponds to ❽ Log): writes a record of this entire Q&A exchange for the permanent record.

**Why the two "eight-step" breakdowns don't align neatly**: Chapter One divided by "what action is performed"; this section divides by "who sends a message to whom." The two framings were never meant to map one-to-one. ❸ Retrieve is a single action but requires two to three separate communications; ❻ Guardrails and ❼ Respond with citations are two actions but share a single return transmission. Same system, different angle, naturally different slicing.

**About step 7: the answer is "streamed" over, not "sent" after it's fully written**

Section 3.3 explained that the model generates token by token. The backend doesn't wait for the entire answer to be complete before sending it back — it pushes tokens to the frontend as they arrive, which is why you see text appearing one character at a time (technically this usually uses SSE or WebSocket).

This creates a real engineering conflict: **streaming output and guardrails are at odds**. If tokens have already been pushed to the user's screen, how can you still "check before releasing"? The practical compromise is to detect problems in-flight while streaming, and the moment something is flagged, immediately interrupt and retract or replace what's already been displayed. This is why you sometimes see an AI's response vanish mid-sentence, replaced by "I'm sorry, I'm unable to answer that question."

**Four points worth remembering**:

1. **The downstream components are mutually unaware of each other's existence.** The vector database doesn't know there's a model service; the reranking service doesn't know there's a logging system — it's the backend that takes the output of one component, translates it into the format the next component expects, and passes it along. The more components there are, the more pronounced this becomes: in the eight steps above, the backend communicates with six different parties, while the number of direct connections among those parties is zero.

2. **All judgment and gatekeeping can only happen at the backend.** It's the only component with full visibility, and it sits within the company's own sphere of control (the model service may well belong to another company entirely). This is why compliance and security review logic must live in this layer — Chapter Five will cover this in detail.

3. **The backend is also responsible for all "what if something goes wrong" handling.** If the model service is rate-limited, should it queue and retry? If retrieval times out, should it degrade gracefully or return an error outright? If a step fails, where should it fall back to? Only the backend can make these calls. In real systems, the code for handling exceptions is often more extensive than the code for the happy path — this is precisely the difference between an "owner" and a "messenger."

4. **Agentic RAG doesn't change this diagram** (covered in detail in Chapter Four). It simply has the backend run steps 2 through 4 for additional rounds, with the number of rounds decided by the model on the fly. The division of labor, who can talk to whom — none of that changes.

[^pagedattention]: Kwon et al., *Efficient Memory Management for Large Language Model Serving with PagedAttention*, SOSP 2023 (the core paper behind vLLM). https://arxiv.org/abs/2309.06180

---

## Chapter Four · Agents: When the Model Starts Deciding and Acting on Its Own

### When You Need an Agent, and When You Don't

The RAG described earlier is a fixed pipeline: retrieve material, assemble, generate — one pass through. For many questions, that's enough.

But some tasks can't be completed in a single pass. Take the AI customer support example again: a customer reports "after upgrading to the new version, a certain feature stopped working." To answer this, the system needs to check whether there are known issues with that version, then look up which configuration the customer is using, and possibly also check whether there are relevant change notes for that specific configuration — and **what to look up in the next step depends on what was found in the previous one**. If the first step already turns up the answer in the known issues list, the remaining steps don't need to happen at all.

This mode of operation — "break the task down on its own, decide the next step on its own, loop until done" — is what an **agent** is. The core distinction from a fixed pipeline is: **how many steps to take, and what to do in each step, is decided by the model on the fly — not hard-coded in advance.**

The flip side also needs to be stated clearly: **simple tasks should not use agents.** For questions that can be answered in a single step, calling the model directly or running a fixed RAG pipeline is better — faster, cheaper, and easier to debug when something goes wrong. The prevailing advice is to start with the simplest fixed pipeline and add complexity only when genuinely necessary. Autonomy has costs, which we'll cover at the end of this chapter.

### ReAct: The Most Common Operating Pattern

The most fundamental and widely used agent pattern is called **ReAct**[^react], named after the paper's title combining Reasoning and Acting. In the original paper, the model's execution trace alternates between three parts:

- **Thought**: based on the information it has so far, the model judges what to do next
- **Action**: the model requests a tool call — querying a database, running a calculation, hitting an API endpoint
- **Observation**: the content returned after the tool executes, fed back to the model by the harness

Note that the first two are produced by the model; the third is fed in from outside. Later references often write these three steps as Reason / Act / Observe to align with the ReAct name — they mean the same thing.

The three steps cycle repeatedly until the model judges the task complete.

ReAct is the default starting point, but not the only pattern. When a task is complex enough that a single loop can't keep up, the model can be made to first decompose the entire task into a plan and then execute each item; when the same type of error recurs, a layer can be added for the model to review its failure reasons. The industry's experience is: **start with ReAct, establish baselines for success rate, tool-call accuracy, latency, and cost; only upgrade once you've confirmed that a single agent genuinely can't solve the problem** — premature complexity is a common and expensive mistake.

### Four Supporting Concepts

**Harness**

The model itself is simply an inference engine that generates output given input context. It doesn't maintain state on its own, doesn't loop on its own, and can't directly execute external operations. What actually organizes the model into an agent is the surrounding runtime layer, typically called the **harness**. The harness drives the model through repeated cycles of thinking, calling tools, receiving results, and continuing to reason, enabling the system to carry tasks through to completion.

Beyond driving this loop, the harness is also responsible for: maintaining the roster of available tools, parsing the model's tool-call requests and actually executing them, deciding what goes into the context window each round (whether old content gets compressed or dropped), retrying on errors, intercepting high-risk actions for human approval, and logging the entire process.

In the language of Section 3.4, **the harness is that "sole active initiator" — the backend**. An agent doesn't change the communication diagram; it just has the backend run some of those steps repeatedly.

The term is borrowed from software testing (a "test harness" is scaffolding that runs code under controlled conditions). It deserves its own name because **the quality of the harness matters as much as the quality of the model**: the same model with a different harness can see task success rates differ by more than double. A significant proportion of enterprise agent projects that fail trace the root cause to harness design, not model capability. Anthropic has a nice way of putting it — every component in the harness encodes an assumption about "what the model can't do on its own"; once the model improves at that thing, the corresponding component should be removed.

**Function Calling (Tool Use)**

The model **does not** actually execute anything. All it can do is output a structured piece of text meaning "I'd like to use the 'search product documentation' tool, with the argument 'legacy data migration'" — and then the harness carries out the execution and relays the result back.

In other words, the model can only **express intent**; it can't even initiate an action on its own — this is the flip side of the rule from Section 3.4: the initiative always stays with the backend. (This capability is now more commonly called "tool use" or "tool calling"; "function calling" is the earlier name.)

**MCP (Model Context Protocol)**

An open standard that specifies the interface tools and data sources should use to connect with an agent. Before it existed, each new tool integration required writing bespoke adapter code; with a unified standard, it's like going from "every appliance with its own proprietary plug" to a USB port.

Two costs are worth knowing about. First, **context cost**: MCP tool descriptions are resident in the context; connect too many servers and a significant chunk of the context window is consumed before the conversation even starts (the industry currently mitigates this with "load tools on demand"). Second, **security**: the MCP specification itself contains no authentication or authorization mechanisms; as of the first half of 2026, dozens of related vulnerability reports have been filed, and any third-party MCP server should be audited before connecting.

**Skill**

A pre-packaged workflow description: a document spelling out how a certain type of task should be done — what phrasing to use, which steps to follow, what counts as done — which the agent follows when needed. In practice it's just a folder containing an instruction file, optionally with templates and reference materials.

The key design is called **progressive disclosure**: normally only the skill's name and a one-sentence description are loaded; only when a task matches does the full content get read into context. So you can install dozens of skills without blowing up the context window.

**Skills and MCP are often confused, but they're actually complementary**: MCP solves "what it can reach" — connecting the agent to external systems; skills solve "how it should work" — teaching it a set of procedures. A skill doesn't connect to anything or execute any calls; it's simply a written set of instructions. Most production-grade agents need both.

### Memory

The model has no memory — Chapter One said as much when explaining Loop C: multi-turn conversation works by stuffing the history back into the context. Agents face the same problem, and it's worse: a task that runs for dozens of rounds produces thinking, tool calls, and return results that quickly exceed what the context window can hold.

So agent memory comes in two tiers:

- **Short-term memory**: what's currently in the context window — the entire process of this task up to the present moment. It has a hard capacity limit, and the harness must continually decide what to keep, what to compress, and what to drop.
- **Long-term memory**: an external store outside the context that persists past experiences, conclusions, and user preferences, retrieving them when needed. **Its implementation is essentially RAG** — except the retrieval target isn't company documents, but the agent's own history.

Memory went from being essentially a synonym for "context window" around 2024 to being recognized as a core architectural layer on par with reasoning, orchestration, and tools — no longer optional.

### Agentic RAG: Handing Retrieval Decisions to the Model

Agentic RAG is the third generation of RAG mentioned in Chapter One.

Its approach applies this chapter's mechanisms to the retrieval step: retrieval is no longer a fixed step three in a pipeline, but becomes a tool the agent can invoke on demand. The model judges for itself whether the material gathered so far is sufficient to support an answer; if not, it adjusts its angle and retrieves another round, repeating until satisfied — this is exactly Loop A from Chapter One.

What must be emphasized: **what changes is not the components, but who's in command.** The vector database, embedding service, reranking service, and generation model are all unchanged; the communication patterns between the backend and these components also remain the same. The sole difference is that "how many retrieval rounds to run, and how to retrieve" shifts from preset, hard-coded rules to the model's real-time judgment during execution.

The cost of this is reduced predictability. Under fixed rules, how many steps a Q&A exchange will take, how many model calls it requires, and how much it will cost are all known in advance. Once the model decides on the fly, these depend on its judgment in the moment, and the model's output is inherently stochastic — the same question might take one retrieval round this time and four the next. Cost, latency, and even the answer itself go from being fixed values to being a range.

### Costs and Risks

**Context snowballs.** With each loop iteration, the harness must resend all preceding thoughts, tool calls, and return results to the model — the input keeps growing; Section 3.3 explained that prefill cost grows quadratically with input length, so this part of the cost rises faster than the number of rounds.

However, this is exactly the scenario where prompt caching shines — each round of an agent's context is the previous round with content appended at the end; the long prefix at the beginning is byte-for-byte identical and can directly reuse previously computed results. Major providers charge roughly one-tenth of the full price for cache-hit portions. This produces a design rule that runs counter to intuition: **place stable content (system instructions, tool descriptions, reference material) verbatim at the beginning, and append all changing content to the end.** Caching requires the prefix to be byte-for-byte identical; change the tool ordering or insert a timestamp in the middle, and the cache misses. It's also not a silver bullet: what gets discounted is only the input portion; the thoughts and tool calls generated each round are output, still billed at full price; the cache itself has an expiration window; and if the harness compresses context mid-task, the prefix changes and the cache is invalidated.

**It may not stop.** The model's ability to judge "the task is complete" is unreliable — it might bounce back and forth between two tools, or fall into an infinite loop. So the harness must enforce hard limits: a maximum number of rounds, a maximum spend, and what to do on timeout.

**Tool failures cascade.** If a tool returns an error or anomalous data, the model may continue reasoning on that basis and veer further and further off course. Production systems need to validate inputs before execution, retry on transient failures, and explicitly tell the model about failures rather than silently skipping them.

**High-stakes actions need human approval.** The most fundamental difference between an agent and a Q&A system is that an agent **actually takes action** — sending emails, modifying data, placing orders. For actions with irreversible consequences, the standard practice is to set up human-approval checkpoints and maintain complete operational audit trails. This should be treated as a first-class component at the architecture design stage, not patched in after an incident. Chapter Five revisits this from a compliance perspective.

**Agents amplify the damage of prompt injection.** If a Q&A system is injected, the worst outcome is a wrong answer; if an agent is injected, it may actually carry out the attacker's desired operation. Chapter Six covers this risk in detail.

[^react]: Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, ICLR 2023. https://arxiv.org/abs/2210.03629

## Chapter Five · The Compliance Perspective: Where Does Confidential Data Actually Go?

When a company's confidential data is processed by an AI system, what risks does that data face at every stop along the pipeline, and how can those risks be mitigated?

Compliance for RAG is thornier than for traditional databases because RAG inherently lacks an audit trail. A single query reads, retrieves, and summarizes across multiple sources within seconds, while regulations like GDPR and HIPAA require companies to account for where personal data is stored and how it's used. Once the system surfaces personal data in an answer where it shouldn't appear, demonstrating compliance after the fact is often extremely difficult. The following breakdown examines risks by the four "states" of data — these four states (at rest, in transit, in use, and residency) reflect generally accepted security concepts, though organizing them as a four-item checklist is this guide's framing, not an official classification from any compliance standard (such as ISO 27001 or SOC 2).

| Data State | Where It Appears | Primary Risks | Mitigations |
|---|---|---|---|
| **① At Rest (data stored and not moving)** | Vectors and original-text chunks in the vector database; model weights after fine-tuning; logs; backups | Original text often sits in plaintext scattered across multiple locations; **vectors have been demonstrated to be reversible back to original text** — an attacker with read access to the vector database can use off-the-shelf tools to reconstruct sensitive content; "stored as vectors" does not mean "de-identified." Weights memorize training data and are difficult to selectively delete | Encryption at rest + customer-managed keys, strict access controls, ensure data can be fully deleted |
| **② In Transit (data moving over the network)** | Every transmission within the system. RAG is inherently distributed — a single query triggers multiple internal transfers (query sent to vector database, document chunks retrieved, chunks forwarded to model); the most critical of these is **the complete prompt being sent to a cloud-hosted model** | TLS (the padlock in the browser bar) only prevents third-party eavesdropping mid-transit — **it does not keep the content confidential from the recipient**. Using a public cloud-hosted model means the confidential original text genuinely leaves the company's boundary and is processed by another company | Self-host or use inference services meeting data sovereignty requirements; redact before sending; clearly define which data must never leave the boundary |
| **③ In Use + Logs (data being processed or being recorded)** | The KV cache held temporarily during inference; the complete prompt and response recorded by the logging platform | **The most easily overlooked yet highly risky**: logs are a persistent plaintext copy of confidential content; if the contract permits, they may also be used for training or retained long-term | Redact before logging; set maximum retention periods (e.g., 30 days); contractually specify usage restrictions |
| **④ Residency + Access (where data lives, who can see it)** | The physical location of each storage and inference component (which country, which legal jurisdiction); access controls when RAG retrieves original documents | Cross-border transfers may violate local regulations; **unauthorized retrieval** — the moment a document is converted into vectors and indexed, its original access permissions are stripped away; without explicitly re-attaching them, the system will retrieve and include content the user has no right to view |  Ensure storage locations are compliant; bind every chunk to the source document's permission list (ACL) at indexing time; filter by querying user's identity in real time during retrieval |

Three points in the table are worth calling out separately, because they are the most counterintuitive and the most likely to become buried risks:

**"Deletion" is often an illusion.** For performance reasons, vector databases default to "soft deletion" at the metadata layer — an API returning no error is taken as successful deletion, but the data may still physically exist; soft-deleted vectors can even be reconstructed. This is the same pain point as "weights are difficult to selectively delete," manifesting at a different storage layer — and GDPR Article 17 requires true, complete deletion.

**Redaction isn't as simple as blacking things out.** Naive redaction destroys semantics: if you simply strip out names or account numbers, the model also loses the information it needs to produce a useful answer — e.g., "Customer ___ 's account ___ was double-charged" becomes unreadable to the model with the blanks. The correct approach is **context-preserving tokenization** rather than brute-force removal: replace "John Smith" with `[NAME_1]` and the specific account number with `[ACCOUNT_1]`, producing "Customer [NAME_1]'s account [ACCOUNT_1] was double-charged." The sensitive values are hidden from the model, but the role information — "there is a name here," "there is an account number here" — is preserved, so the model can still follow the sentence structure and produce a useful answer, instead of staring at a bunch of blanks.

**Permissions are lost by default.** Documents from Confluence, SharePoint, or an internal wiki — once converted into vectors, their original access controls no longer travel with them. This is precisely why "binding ACLs" must be done as an explicit additional step — it does not happen automatically.

None of this is alarmist. OWASP listed "Vector and Embedding Weaknesses" as a newly added standalone category in its 2025 edition[^owasp], and placed prompt injection as the number-one risk for LLM applications — and RAG is precisely the architecture with the largest attack surface.

**Two conclusions most worth remembering**:

1. The **single most sensitive action** across the entire pipeline is the moment confidential content is assembled into a complete prompt and sent to a cloud-hosted model — this is the point at which data truly leaves the company's control.
2. The **single most easily overlooked risk point** is the logging system — all the attention goes to "is the database secure," while forgetting that the logs also contain a complete plaintext copy of every conversation.

**Further reading: what does a managed cloud model (MaaS) actually retain?**

MaaS (Model-as-a-Service) refers to cloud-hosted models accessed via network calls, as opposed to self-hosted deployments. What it actually retains is a key compliance question:

- **Weights are read-only**: the content of your queries does not get written into the model's parameters or change the model itself. "The model has its own storage" is a common misconception — unless the provider deliberately uses conversations for subsequent training, which is a separate matter.
- **Prompt caching is an easily overlooked short-term landing point**: if the provider enables cross-request prompt caching (see Section 3.3), a portion of the request content resides briefly in their infrastructure in the form of KV cache. This is not the same as training or long-term retention, but strictly speaking, inference is not entirely stateless.
- **What is actually retained long-term** is logs (complete Q&A plaintext), abuse-detection records, and (when the contract allows) data used for training — whether it's retained, and for how long, depends on contract terms and technical settings.
- **ZDR (Zero Data Retention)**: a contract clause that, once signed, disables the persistent retention described above. But you should verify whether it covers infrastructure-level short-term residency like prompt caching, to avoid leaving a gap.

[^owasp]: OWASP GenAI Security Project, *OWASP Top 10 for LLM Applications 2025* — LLM08:2025 Vector and Embedding Weaknesses, a newly added standalone category relative to the 2023 edition. The list itself was published November 2024. https://genai.owasp.org/llm-top-10/

## Chapter Six · Beyond RAG: The Full Landscape of LLM Systems

The first five chapters gave a thorough account of RAG, but a reminder is in order: **RAG is just one of many ways to use an LLM**, specifically designed for "knowledge" problems. In the real world, there are several other ways to put LLMs to work, each addressing a different kind of need. This chapter surveys these forms and situates RAG within the broader picture, along with its boundaries of applicability.

To distinguish these forms, start from a concrete scenario: when you have a task and are about to hand it to the model, ask one question first — **to complete it, what is the model missing?** Is it missing knowledge, or autonomous judgment, or a certain capability? Following this question downward, the five forms below each correspond to a specific situation.

**The task doesn't require external knowledge → Use the prompt directly**

Translation, rewriting, summarizing text you've pasted in, generating a passage to spec — these tasks either draw on what the model already knows or don't involve "knowledge" at all; they're pure language processing. In these cases, no additional mechanism is needed — just write clear instructions and hand them to the model. This is also the highest-volume category in everyday use.

**The material is at hand and modest in size → Long context**

If the answer lives in a few documents and those documents, taken together, fit inside the model's context window, then the simplest approach is to drop them all into the prompt and let the model read them directly. By 2026, frontier models have context windows in the million-token range; a manual of several hundred pages can be loaded in its entirety, with no need for chunking or retrieval. The cost is that every question requires rereading all the material from scratch — once the volume grows, this gets both slow and expensive, and the longer the material, the more likely the model is to overlook key details.

**Too much material to fit → RAG**

When the knowledge base is too large to fit in the context (thousands upon thousands of documents, continuously updated), you have no choice but to first "search" for the relevant passages and then feed those to the model — this is exactly the RAG covered in the preceding five chapters. Its essence: use retrieval to winnow "too much" down to "just right." RAG and long context are thus two solutions to the same knowledge problem; the dividing line is simply whether the material fits.

**What's missing isn't material, but the judgment of "what to do next" → Agent**

Some tasks stall not because of missing knowledge, but because they can't be completed in one shot — you need to look up this first, then based on what you find decide to look up that, and perhaps even take real actions in external systems. What's needed here is for the model to plan, invoke tools, and drive the process forward in a loop — in other words, the agents from Chapter Four. According to a Gartner prediction[^gartner], by the end of 2026 40% of enterprise applications will feature task-specific agents, up from less than 5% a year earlier.

**What's missing is a capability or behavior itself → Fine-tuning**

The preceding forms all leave the model unchanged. But if the problem is that the model's behavior is wrong — inconsistent output formats, a tone that doesn't match requirements, poor performance on a specialized task type (e.g., ticket classification, SQL generation for a specific schema) — then you need the fine-tuning from Chapter Two to press stable behavior into the model's weights. Remember the dividing line: **fine-tuning governs form; RAG governs facts** — use retrieval for knowledge that changes, fine-tuning for behavior that should be stable.

**The art of feeding material: context engineering**

Once you've chosen the route of feeding material to the model (long context, RAG, or agent-embedded retrieval), a new question arises: context window space is limited, and retrieved material, conversation history, tool return values, and long-term memory all compete for room — which pieces to include, how to arrange them, when to compress or discard — these directly determine the model's performance. Managing this is called **context engineering** — it's the evolution of "prompt engineering," concerned no longer with "how to write a good instruction" but with "how to organize all the information the model sees at once." As systems grow more complex, this layer is shifting from an afterthought optimization to a core decision that must be addressed at the architecture design stage.

**Summary: which form to choose depends on what you're missing**

Given a task, run through the checklist and the approach becomes clear: missing knowledge means supply material (modest volume → long context; large volume → RAG); needs multi-step autonomy → agent; unstable behavior → fine-tuning. Missing one thing, supply one thing; missing several, stack several — real systems are mostly assembled on-demand from combinations like these, rather than being a single form.

The RAG covered throughout this guide is the most commonly used and most accessible-to-understand section of this map, but it's ultimately just one piece — and more often than not, it's used in combination with the other forms.

[^gartner]: Gartner, *Gartner Predicts 40% of Enterprise Apps Will Feature Task-Specific AI Agents by 2026, Up from Less Than 5% in 2025*, press release, August 26, 2025. https://www.gartner.com/en/newsroom/press-releases/2025-08-26-gartner-predicts-40-percent-of-enterprise-apps-will-feature-task-specific-ai-agents-by-2026-up-from-less-than-5-percent-in-2025

## Appendix · Toolkit Overview

Below, organized by pipeline stage, are common tools and platforms as of 2026, listed for reference. This field moves fast — the maintenance status, naming, and pricing of specific tools can change at any time, so verify before making production decisions.

**By pipeline stage (common tools/platforms for each)**:

| Stage | What This Step Does | Common Tools / Platforms |
|---|---|---|
| Document parsing / chunking | Reading formats like PDF and Word into text, and splitting into small segments | Unstructured, LlamaParse, LlamaIndex's loader ecosystem, Docling |
| Embedding models | Converting text into vectors | OpenAI embeddings, Cohere, BGE, Voyage, sentence-transformers |
| Vector databases | Storing vectors and performing similarity search | Pinecone, Weaviate, Milvus, Chroma, Qdrant, pgvector |
| Reranking models | Precision-ranking rough-screened results, keeping only the most relevant few | Cohere Rerank, BGE-reranker, Jina Reranker |
| Orchestration / RAG frameworks | Development frameworks that wire the entire pipeline together | LangChain, LlamaIndex, Haystack, RAGFlow |
| Agent frameworks | Development frameworks supporting ReAct loops and multi-agent collaboration | LangGraph, AutoGen, CrewAI |
| Inference serving | Running large models and exposing them as a service | vLLM, TGI (Text Generation Inference), SGLang |
| Evaluation | Measuring how well a RAG/Agent system performs | RAGAS, DeepEval, TruLens, promptfoo |
| Observability | Logging, tracing, and debugging the entire system's operation | LangSmith, Langfuse, Arize Phoenix |

("Reranking models" correspond to the precision-ranking stage of the Section 3.2 funnel; "evaluation" and "observability" correspond to the log-feedback mechanism described in Chapter One's Loop D — the tools are simply off-the-shelf products that implement these mechanisms.)

**By brand ecosystem (product suites from the same company/community)**:

- **LangChain family**: LangChain (base framework) + LangGraph (purpose-built for agent orchestration) + LangSmith (observability / debugging) — three products within the same ecosystem designed to work together.
- **Hugging Face family**: the Model Hub (the world's largest open-source model repository) + Transformers (a library for conveniently loading various models) + TGI (inference serving) + a full suite of open-source tools.
- **Cloud-provider MaaS**: AWS Bedrock, Azure AI Foundry, Google Vertex AI, and similar services package embedding and generation models as managed cloud services, allowing enterprises to make API calls without building their own servers.

---

## Quick Reference (Core Takeaways for a Final Review)

- **Embedding**: turns semantic meaning into a position in space — the more similar the meaning, the closer the positions. The indexing side and the query side must use the same model.
- **Retrieval is a "wide-to-narrow funnel"**: vector search (by meaning) paired with keyword search (by literal text) running in parallel → filter by permissions and timeliness → precision reranking. Vectors excel at semantics but not at exact literal matches, so in most scenarios the two tracks complement each other and work best together.
- **ANN (Approximate Nearest Neighbor)**: trades a small amount of accuracy for a massive speed gain. HNSW is the default choice (the graph must fit in memory); for very large datasets, use IVF or DiskANN.
- **Inference has two phases**: prefill reads the entire input in parallel (compute-bound); decode generates one token at a time (memory-bandwidth-bound). Total wait time is usually dominated by decode.
- **KV cache**: trades GPU memory for eliminated redundant computation, bringing quadratic computation down to near-linear; prompt caching further allows reuse of identical prefixes across requests.
- **System communication**: the backend / orchestration layer is the only party that actively initiates actions; the vector database, model services, reranking service, and other downstream components never communicate with each other directly — all coordination runs through the backend.
- **Compliance**: the single most sensitive moment is when confidential content is assembled into a prompt and sent to a cloud-hosted model; logs are the most easily overlooked plaintext retention point.
- **Agents**: Thought → Action → Observation in a continuous loop; the model is the brain, the harness is the body — the quality of the harness matters as much as the model.
- **Generational distinction**: when the loop rules are hard-coded, it's classic RAG; when "whether to search again, and how" is handed to the model to judge on the fly, that's agentic. What changes is not the components, but who's in command.
- **The full landscape**: RAG is just one of many LLM usage patterns. Missing knowledge → supply material (modest volume with long context, large volume with RAG); missing autonomy → agent; missing capability or behavior → fine-tuning. Which form to choose depends on what the task is missing.
