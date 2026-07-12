
**The core problem RAG solves.** A language model only knows what it learned during training. That means it doesn't know your company's documents, anything that happened after its training cutoff, or any private data — and when it doesn't know something, it often makes up a confident-sounding wrong answer (a "hallucination"). RAG (Retrieval-Augmented Generation) fixes this by _looking things up first_. Before the model answers, you fetch the relevant documents and hand them to it, so it answers from real information instead of memory.


**RAG vs fine-tuning vs in-context learning.** These are three ways to make a model "know" something, and they're easy to mix up.

**_In-context learning_** is just putting information directly in your prompt ("Here are the rules, now answer this"). Simple and instant, but limited by how much text fits in one prompt.

**_Fine-tuning_** means actually retraining the model on your data so the knowledge gets baked into its weights. It's like sending it to school — good for teaching a _style_ or _skill_ (always answer like a lawyer, always output this format), but expensive, slow to update, and bad for facts that change.

**_RAG_** keeps the model as-is and feeds it fresh information at question time. It's the open-book approach — great for facts that change often, easy to update (just add a document), and it can cite its sources.


**The indexing pipeline**
- _Ingest_ — gather your raw sources (PDFs, web pages, docs, databases).
- _Parse_ — extract the actual text out of those messy formats.
- _Chunk_ — cut long documents into bite-sized passages, because you can't embed a whole book as one vector and you only want to hand the model the relevant paragraph, not the entire file.
- _Embed_ — turn each chunk into a vector (its "meaning fingerprint").
- _Store_ — save those vectors in a vector database so they're searchable.


**The query pipeline** (runs every time someone asks — using the library):
- _Query_ — the user asks a question.
- _Embed_ — turn that question into a vector, using the same model as the chunks.
- _Retrieve_ — find the chunks whose vectors are closest to the question.
- _Rerank_ — take those candidates and reorder them with a smarter (slower) model that reads the question and each chunk _together_, pushing the truly best ones to the top.
- _Generate_ — hand the top chunks plus the question to the language model, which writes the final answer from them.


**Naive vs Advanced vs Modular RAG.** These describe how sophisticated the setup is.

_Naive RAG_ is the basic version — embed, retrieve top matches, stuff them in the prompt, generate. Quick to build, and often "good enough," but it retrieves whatever is closest even if it's a poor match, and struggles with vague or complex questions.

_Advanced RAG_ adds tune-ups around that same pipeline to fix its weak spots: cleaning up the query before searching, adding reranking, smarter chunking, hybrid keyword-plus-semantic search. Same shape, better quality at each step.

_Modular RAG_ is the flexible, grown-up version where the pipeline becomes rearrangeable building blocks. The system can loop, make decisions, and route differently per question — for example, decide whether it even _needs_ to retrieve, search multiple sources, or retrieve again if the first answer looks weak. Less a fixed line and more a system that adapts.


**Fixed-size chunking**
The simplest approach: cut the text every N characters or tokens, regardless of content. Fast, predictable, trivial to implement.

**Recursive character text splitter**
This is the sensible default for most text, and the one most RAG tutorials use. Instead of one hard cut point, it tries a _list_ of separators in priority order — paragraphs first, then lines, then sentences, then words — splitting on the biggest natural boundary that keeps chunks under your size limit.

**Sentence-aware chunking**
A step up in respecting structure: split into complete sentences (using a proper sentence tokenizer, not just splitting on periods, which chokes on "Dr." and "3.14"), then group sentences together until you approach your size limit. Every chunk starts and ends on a clean sentence boundary.

**Semantic chunking**
The most sophisticated of the general strategies. Instead of chunking by size at all, you chunk by _meaning_: embed each sentence, then walk through the document looking for points where the topic shifts (where consecutive sentence embeddings suddenly become dissimilar), and cut there. The result is chunks whose boundaries fall at natural topic changes, so each chunk is genuinely about one subject

**Markdown-aware chunking**
When your source has explicit structure — Markdown headers, sections — you should chunk _along that structure_ rather than fighting it. A Markdown-aware splitter breaks at headings, so each chunk is a logical section, and it can carry the header hierarchy along as context.

**Code-aware chunking**
As mentioned in the parsing section, splitting code by size is destructive — it cuts functions in half. Code-aware chunking uses the syntax tree (via `tree-sitter`) to chunk on real boundaries: one chunk per function, method, or class, keeping each unit whole.