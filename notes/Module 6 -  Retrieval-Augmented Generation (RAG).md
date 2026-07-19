
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

Multi-query retrieval

The problem: a single query is a single point in embedding space, so it only "sees" one neighborhood. If the user phrases their question differently from how the documents are written, the right chunks may sit just outside that neighborhood and never get retrieved. One phrasing, one blind spot.
Multi-query retrieval fixes this by using an LLM to rewrite the user's question into several alternative phrasings, then retrieving for each one and merging the results. "How do I make search faster?" might become "techniques to speed up vector search," "reducing query latency in ANN," "approximate nearest neighbor performance" — each lands in a slightly different part of the space, and together they cover far more relevant ground.

Corrective RAG (CRAG)

Multi-query improves what you retrieve but still trusts it blindly. CRAG adds a quality check on the retrieved chunks before generation, and a fallback when they're bad.
The flow: retrieve as usual, then a lightweight "retrieval evaluator" grades whether the chunks are actually relevant to the question. Based on that grade, it branches:

Correct (chunks look good) → use them, optionally after refining them (stripping the irrelevant sentences out of otherwise-good chunks).
Incorrect (chunks are off-topic) → discard them and fall back to another source, typically a web search, so the model isn't forced to answer from irrelevant context.
Ambiguous (not sure) → do both: combine the retrieved chunks with web results.


Self-RAG
`
Self-RAG is the most ambitious: it trains the model to decide for itself when to retrieve, and to critique its own output as it generates, using special "reflection tokens." Rather than retrieval being a fixed step that always happens, the model treats it as a tool it invokes on demand and then judges the results of.
During generation the model emits little control signals that answer questions like: Do I even need to retrieve here? (some questions are answerable from its own knowledge — retrieving would just add noise); Are these retrieved passages relevant?; Is my draft sentence actually supported by them?; and Is this a good, complete answer? It uses these self-assessments to retrieve only when useful, to keep only supporting passages, and to check that its claims are grounded in the sources rather than hallucinated.
The distinguishing features are two: retrieval is adaptive (on-demand, not always), and the model does self-critique for groundedness — it verifies its own statements against the evidence. The catch is that this generally requires a specially trained model (the reflection behavior is fine-tuned in, not just prompted), which makes it heavier to adopt than the other two. Its payoff is fewer needless retrievals and answers that stay tethered to the sources.


Why reranking improves precision
Your first-stage retriever (vector search) is optimized for speed at scale — it has to compare the query against millions of vectors, so it uses a representation that's cheap to compare but a bit coarse. That gets you good recall (the right chunk is probably somewhere in the top 50) but mediocre precision (it might be ranked 23rd, not 1st).
A reranker only has to look at ~50 candidates, so it can afford to be far more thorough — reading the query and each document together and judging actual relevance rather than rough vector proximity. That's why the two-stage design wins: you get the retriever's scale and the reranker's accuracy, without paying the reranker's cost across your whole corpus. And because you typically feed only the top 3–5 into the LLM, getting the ordering right matters — reranking is what makes sure the chunks the model actually sees are the best ones

Cross-encoder vs bi-encoder
This is the mechanism that makes reranking more accurate, and it's really an architecture difference.The difference is when the query and document meet. A bi-encoder (what your vector search uses) encodes them separately; a cross-encoder (what a reranker uses) reads them together.

The bi-encoder's separation is what makes vector search possible — because documents are encoded independently, you can embed them all ahead of time and just compare vectors at query time. But that independence is also its weakness: the model never sees the query and document side by side, so it can't notice subtle interactions between them.
The cross-encoder gives up that precomputation. It feeds the query and document into the model together, so its attention can flow across both and directly judge "does this document answer this query?" That's far more accurate — but you can't precompute anything, because the score depends on the specific pair. You'd never run it over a million documents. Run it over 50, though, and it's both affordable and dramatically better. That's the whole reason for the two-stage funnel: bi-encoder to narrow a million to fifty, cross-encoder to order those fifty.


The Four Core Metrics

Faithfulness — does the generated answer only contain claims supported by the retrieved context? RAGAS does this by breaking the answer into individual statements, then checking each one against the context with an LLM judge. Low faithfulness = hallucination, even if retrieval was good. This is the direct measure of whether your grounding instructions (from last time) are actually working.
Answer Relevancy — does the answer actually address the question asked, independent of whether it's grounded? Measured by generating several hypothetical questions the answer would answer, then comparing their embedding similarity to the original question. Catches answers that are technically true and grounded but off-topic or evasive.
Context Recall — of everything needed to answer the question, how much did retrieval actually surface? This one requires a reference/ground-truth answer to compare against, since you need to know what "complete" looks like. Low recall means your retriever is missing relevant chunks — a chunking or embedding problem, not a generation problem.
Context Precision — of what was retrieved, how much was actually relevant (and was it ranked near the top)? High precision means your top-k isn't cluttered with irrelevant chunks that dilute the generation prompt. This is where you'd catch a bad k value or a similarity threshold that's too loose.

A useful mental model: Recall + Precision are about your retriever (Qdrant + embeddings), Faithfulness + Relevancy are about your generator (the prompt + LLM). When scores are bad, this split tells you which half of your pipeline to fix.
Building a Golden QA Dataset
This is a curated set of (question, expected answer, ideally expected source chunks) triples that you treat as ground truth for evaluation. Context Recall and any reference-based metric depend on having this.
Practical approach for your project: pull a sample of chunks from your indexed PDFs, manually (or with an LLM assist) write questions that chunk should answer, and record the expected answer plus which chunk(s) it should come from. Aim for variety — factual lookup questions, multi-document synthesis questions, and a few "shouldn't be answerable" questions to test your missing-context handling. Even 20-30 well-constructed examples is enough to start catching regressions as you tune chunking or retrieval params.
TruLens
An alternative/complementary evaluation framework to RAGAS, built around the idea of "feedback functions" — small LLM-graded or rule-based scorers you attach to a pipeline. Its signature contribution is the RAG Triad: Context Relevance (retrieval quality), Groundedness (equivalent to faithfulness), and Answer Relevance — conceptually the same idea as RAGAS's metrics, just packaged differently. TruLens leans more into tracing/observability — logging every step of a chain and visualizing scores per-run in a dashboard, which is handy if you want to inspect why a particular query scored low rather than just getting a number. Worth knowing both exist; picking one is mostly about whether you want a lightweight scoring library (RAGAS) or a fuller tracing/dashboard setup (TruLens).
Chunking Ablation Studies
Since chunking strategy directly drives what Context Recall/Precision look like, an ablation study means systematically varying chunking parameters and re-running your golden dataset through evaluation to see what moves the needle:

Chunk size (e.g., 256 vs. 512 vs. 1024 tokens)
Overlap (0% vs. 10% vs. 20%)
Splitting strategy (fixed-size vs. sentence-aware vs. semantic/embedding-based splitting)

You hold everything else constant (same embedding model, same retriever, same k) and only vary the chunking config, then compare Context Recall/Precision across runs. This is exactly the kind of experiment your "additional chunking strategies" next-step would feed into — once you have RAGAS wired up, ablation is just re-running evaluate() per config and tabulating results.
Retrieval@K Metrics
Standard information-retrieval metrics applied to your Qdrant results, independent of the LLM:

Recall@K — of all truly relevant chunks in your corpus, what fraction appear in your top-K results?
Precision@K — of your top-K results, what fraction are actually relevant?
MRR (Mean Reciprocal Rank) — how high up was the first relevant chunk, averaged across queries? (1/rank, so a relevant chunk at position 1 scores 1.0, at position 3 scores 0.33)
NDCG@K — like Recall@K but rewards relevant chunks appearing higher in the ranking, not just present somewhere in the top-K.

These are cheaper to compute than RAGAS's LLM-judged metrics (pure vector math against your golden dataset's known-relevant chunks, no LLM calls needed) so they're good for fast iteration when tuning k or comparing embedding models, before you spend the API budget on a full RAGAS faithfulness/relevancy pass.