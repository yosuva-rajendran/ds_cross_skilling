
**LLM Fundamentals**
1. **LLM** :
		A Large Language Model is, at its core, a next-token predictor.
		It's a neural network (transformer architecture) trained on enormous amounts of text
		it's single job is given a sequence amount of tokens, predict the probability distribution over what token comes next. 
		Generate one token, append it, repeat. That's it.

2. **Tokens** :
		tokens are the units the model actually operates on(subword pieces produced by a tokenizer)
		Tokens are counts against model's context window.

3. **Context window** :
		means maximum number of tokens the model can see at once.(input + output combined)
		More text sent to the model = more tokens processed
		model has to read everything in the context window before answering
		models tend to pay less attention to information buried in the _middle_ of a very long context (the "lost in the middle" effect)

4. **Temperature & randomness :**
		Before the model chooses a word, it assigns a **score** to every possible token. These raw scores are called **logits**.
		Humans understand probabilities better than raw scores.**Softmax** converts logits into probabilities that add up to 100%.
		Once probabilities exist, the model needs to pick a token.This process is called **sampling**.
		Temperature changes the logits **before softmax**.

5. **Hallucination :**
		LLMs don't naturally know when they're wrong.
		A hallucination happens when an AI gives an answer that sounds correct and confident but is actually wrong or made up.
		reasons: ambiguous prompts, topics outside training data, asking for exact details it can't verify

6. **Determinism vs creativity** :
		deterministic means gives same output for same input (temperature = 0)
		creativity: the model is allowed to explore different possibilities.(temperature = 1.0)

7. **Base vs instruction-tuned vs chat models** :
		Base: trained purely on next-token prediction over raw text. It will continue your prompt rather than answer it.
		instruction-tuned: the base model is further fine-tuned (**supervised fine-tuning**, SFT) on datasets of (instruction → ideal response) pairs, teaching it to actually follow commands.
		Chat model: builds on instruction-tuning with conversational structure (system/user/assistant turns) and typically RLHF (**reinforcement learning** from human feedback) to align it toward being helpful, harmless, and honest in dialogue

**Model Ecosystem**

1. **Closed-source vs open-source models**
		closed-source (GPT, Claude, Gemini) gives you **state-of-the-art** capability via API with zero infrastructure burden, but you can't run it locally, fine-tune the weights directly, or fully control data residency.
		Open-source/open-weight models (Mistral, Llama, Phi) can be self-hosted, fine-tuned, and run offline, at the cost of needing your own GPU infrastructure and typically trailing the absolute frontier in capability.

**Benchmarks — How Models Get Measured**

1. **MMLU** (Massive Multitask Language Understanding):
	   a multiple-choice exam spanning 57 subjects — law, medicine, math, history, etc. It's a good proxy for broad factual/reasoning knowledge, but it's multiple-choice, so it doesn't test open-ended generation quality.

2. **HumanEval**
		164 hand-written programming problems where the model writes a function and it's checked against unit tests
		Directly relevant to you for evaluating code-gen capability.

3. **Reading a model card**:
		The parts worth actually reading: **_intended use cases and limitations_** (what it's designed/not designed for), **_training data cutoff_** (how recent its knowledge is), **_evaluation results_** (benchmark scores, often including the ones above), **_modality support_** (text/vision/audio), and **_safety/bias considerations_**.


**Model Capabilities**

1. Text generation
	   **Text generation** is the baseline — drafting, summarizing, rewriting

2. **Code generation**
		**Code generation** is the same underlying capability applied to programming languages, now good enough for autocomplete, full functions & agentic coding
3. Vision
		**Vision** lets a model accept images alongside text — reading screenshots, diagrams, charts, or UI mockups.
		
4. **Audio** 
		**Audio** capabilities cover speech-to-text (transcription) and text-to-speech (synthesis), sometimes natively in the model, sometimes via separate specialized models.
		
5. **Embeddings**
		the model converts text into a vector (a list of numbers) that represents its meaning, such that semantically similar text produces similar vectors
		ex: RAG systems
		
6. **Function calling / tool use**
		it should call an **external function** and return structured arguments for you to execute.This is the foundation of agentic workflows.
		
7. **Document understanding**
		means feeding the model PDFs, spreadsheets, or other documents directly, often combined with vision for scanned content
8. **Structured output generation**
		means constraining the model's response to a specific format. Typically JSON matching a schema


**Key Model Parameters**

1. max_tokens : Controls the **maximum length of the response**.
2. top_p: Controls how many probable tokens are considered
3. top_k: Limits the model to the **K most likely tokens**.
4. stop sequences: generation stops when the expectes string is produced
5. seed: Attempts to make outputs more consistent across runs.
6. frequency_penalty: Reduces repetition of tokens already used many times.
7. presence_penalty: Encourages introducing **new topics or words**:
8. system(Highest-level instructions.) , user(The human's message.) , assistant(is the model's prior responses)