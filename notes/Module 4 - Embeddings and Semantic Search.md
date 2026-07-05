
**What an embedding is**

An embedding is a list of numbers (a _vector_) that represents a piece of data (word, sentence, image). 
the numbers aren't random or arbitrary: they're arranged so that _geometry carries meaning_.

**Why embeddings capture semantic meaning**

The foundation is the _distributional hypothesis_, often summed up as "you shall know a word by the company it keeps." Words and sentences that show up in similar contexts tend to mean similar things.

Embedding models are trained on prediction tasks over enormous amounts of text: predict the masked-out word, predict the next token, or judge whether two sentences genuinely belong together. To get good at these tasks, the model is _forced_ to squeeze the context of each item into its vector. As a side effect, items that get used the same way drift toward similar vectors. Meaning is never explicitly programmed in it emerges from the training objective.

**Embedding space and clustering**

![[Pasted image 20260705160924.png|697]]

Similarity is usually measured with **cosine similarity** — the angle between two vectors rather than the straight-line distance, which behaves better in high dimensions.
Two big families of operations fall out of this: _clustering_ (algorithms like k-means or HDBSCAN group nearby points into themes automatically) and _nearest-neighbor search_ (given a query point, find the closest points to it).

**Sparse vectors (TF-IDF, BM25) vs dense vectors**
![[Pasted image 20260705162621.png]]

**Sparse vectors** are basically word-counting. Picture a giant checklist with one box for every word in the dictionary — tens of thousands of boxes. For a given sentence, you tick the boxes for the words it actually contains and leave the rest at zero. Since any one sentence only uses a few words, almost every box stays empty ("sparse" just means "mostly zeros"). TF-IDF and BM25 are smart versions of this counting: they give more weight to rare, distinctive words (like "photosynthesis") and less to common ones (like "the").

The catch: this only knows _exact words_. To a sparse vector, "car" and "automobile" are as unrelated as "car" and "banana," because they're different boxes on the checklist. Great for matching keywords and names, blind to meaning.

**Dense vectors** are the opposite. Instead of one box per word, you get a short list — a few hundred numbers — where every number carries meaning, learned by a neural network from reading tons of text. There are no empty boxes; the whole list is "packed" ("dense"). Because the numbers represent _meaning_ rather than _spelling_, "car" and "automobile" come out looking almost identical.

The catch: you need a trained model to make them, and you can't look at the numbers and understand what they mean — they're not human-readable.

**Use cases**

**Search.** Embed your documents once and store them; at query time, embed the query and return its nearest neighbors. Unlike keyword search, this finds results by meaning, so "how do I fix a flat tire" can surface a doc titled "repairing a punctured wheel."

**Clustering.** Run a clustering algorithm over embeddings of unlabeled data to discover structure automatically — grouping support tickets by topic, segmenting customers, or de-duplicating near-identical items.

**Classification.** Use embeddings as input features to a lightweight classifier (even simple logistic regression). Because the embedding already encodes meaning, you can build accurate spam filters, sentiment or intent detectors with relatively few labeled examples.

**RAG (retrieval-augmented generation).** This is the big one for LLM applications. You split your documents into chunks, embed each chunk, and store them in a vector database. When a user asks a question, you embed the question, retrieve the top-k most similar chunks, and paste them into the LLM's prompt as context. The model then answers using _your_ data — which reduces hallucination, keeps answers current, and lets the model reference information it was never trained on.



**Embedding Models**

**Specialized embeddings (different kinds of data)**

**Code embeddings.** General text models understand code poorly, so there are models trained specifically on source code (e.g. Voyage's code models, Jina's code embeddings, and others). They place semantically similar code near each other regardless of variable names, which powers code search and "find similar function" features.

**Image embeddings — CLIP.** CLIP (from OpenAI) is special because it embeds _images and text into the same space_. That means the vector for a photo of a dog sits near the vector for the words "a dog," so you can search images with text queries or do zero-shot image classification. Common variants output 512 or 768 dimensions. Later relatives include OpenCLIP and SigLIP.

**Embedding dimensions — what 768 / 1536 / 3072 actually mea**n

The dimension count is simply how many numbers are in each vector. More dimensions give the model more room to encode subtle distinctions, so higher-dimensional embeddings _tend_ to be more accurate — but with real costs: they take more storage, more memory, and make nearest-neighbor search slower (roughly proportional to the dimension count). Doubling from 1536 to 3072 roughly doubles your storage and search cost.




**Similarity and Distance Metrics**
![[Pasted image 20260705164847.png|673]]
**Cosine similarity**
Cosine similarity measures the angle between two vectors and ignores their length entirely. Two vectors pointing the same way score 1.0 no matter how long they are; perpendicular vectors score 0; opposite vectors score −1.

**Euclidean (L2) distance**
Euclidean distance is the straight-line gap between the two vector tips — the ruler measurement from ordinary geometry.

**dot product** = multiply matching numbers, add them up, and the total rewards vectors that both point the same way and are large.

