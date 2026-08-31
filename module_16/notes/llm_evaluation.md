# Module 16: LLM Evaluation

## Why Evaluate?

LLM outputs are non-deterministic. You change a prompt, swap a model, update context —
does it still work? Without evaluation, you're guessing.

Evaluation tells you:
- Is the new prompt better or worse?
- Does the cheaper model produce acceptable quality?
- Are we hallucinating more after the last change?
- Is the system ready for production?

## Evaluation Fundamentals

### Reference-Based vs Reference-Free
- **Reference-based:** Compare output against a known correct answer (golden answer)
- **Reference-free:** Judge quality without a reference (coherence, helpfulness, safety)

### Automated vs Human
- **Automated:** Fast, cheap, scalable. Use metrics or LLM-as-judge
- **Human:** Slow, expensive, but highest quality. Use for final validation

### When to Evaluate
- After changing prompts
- After swapping models
- Before deploying to production
- On a regular schedule (regression testing)

## Text Metrics

### Exact Match
Did the output exactly match the expected answer?
Best for classification, yes/no questions, structured outputs.

### ROUGE (Recall-Oriented Understudy for Gisting Evaluation)
Measures overlap between generated text and reference:
- **ROUGE-1:** Unigram overlap (individual words)
- **ROUGE-2:** Bigram overlap (word pairs)
- **ROUGE-L:** Longest common subsequence
- Good for summarization evaluation

### BLEU (Bilingual Evaluation Understudy)
Measures precision of n-gram overlap. Originally for translation.
Less used for LLM eval now, but still common in benchmarks.

### BERTScore
Uses BERT embeddings to compute semantic similarity.
Better than ROUGE for paraphrases ("dog" vs "canine" score high).

## LLM-as-a-Judge

Use a strong LLM to evaluate another LLM's output.

### Pointwise Scoring
Rate a single response on a scale:
```
"Rate this answer 1-5 on helpfulness, accuracy, and completeness."
```

### Pairwise Comparison
Compare two responses:
```
"Which response better answers the question? A or B?"
```

### Judge Prompt Tips
- Be specific about criteria
- Provide a rubric (what does 5/5 look like?)
- Ask for reasoning before the score
- Watch for biases: position bias (A preferred over B), verbosity bias (longer = better)

## Hallucination Detection

### Types
- **Factual:** Claims something false ("Python was created in 2005")
- **Faithfulness:** Says something not in the provided context (RAG hallucination)
- **Reasoning:** Correct facts but wrong conclusion

### Detection Methods
- **SelfCheckGPT:** Generate multiple responses, check consistency. Inconsistent = likely hallucinated.
- **Entailment check:** Does the context entail (support) the claim?
- **FactScore:** Break response into claims, verify each one.

## Evaluation Datasets

A good eval dataset has:
- 50-200 diverse examples
- Clear expected outputs or scoring criteria
- Edge cases and adversarial examples
- Versioned and maintained

### Building One
1. Collect real user queries from logs
2. Add expected answers (golden dataset)
3. Include edge cases: ambiguous, out-of-scope, adversarial
4. Version it alongside your code

## Regression Testing

Run evals in CI/CD:
1. On every prompt change, run eval suite
2. Compare scores against baseline
3. Fail the build if quality drops below threshold
4. Track trends over time

## Frameworks

| Tool | Best For |
|------|----------|
| OpenAI Evals | OpenAI model eval |
| DeepEval | Python-native, many built-in metrics |
| Promptfoo | CLI-based, multi-provider |
| RAGAS | RAG-specific evaluation |
| Braintrust | Production eval + logging |
