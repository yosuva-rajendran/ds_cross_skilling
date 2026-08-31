"""
LLM evaluation demo: ROUGE scores, exact match, LLM-as-judge,
and a simple eval runner against a golden dataset.
No external eval framework — just Python + one LLM call for judge.
"""

import os
import re
import sys
from collections import Counter
from dotenv import load_dotenv
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


# --- Metrics ---

def exact_match(predicted, expected):
    return predicted.strip().lower() == expected.strip().lower()


def rouge_1(predicted, reference):
    """ROUGE-1: unigram overlap (F1 score)."""
    pred_tokens = predicted.lower().split()
    ref_tokens = reference.lower().split()
    pred_counts = Counter(pred_tokens)
    ref_counts = Counter(ref_tokens)

    overlap = sum((pred_counts & ref_counts).values())
    precision = overlap / len(pred_tokens) if pred_tokens else 0
    recall = overlap / len(ref_tokens) if ref_tokens else 0

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def rouge_2(predicted, reference):
    """ROUGE-2: bigram overlap (F1 score)."""
    def bigrams(tokens):
        return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens)-1)]

    pred_bi = Counter(bigrams(predicted.lower().split()))
    ref_bi = Counter(bigrams(reference.lower().split()))

    overlap = sum((pred_bi & ref_bi).values())
    precision = overlap / sum(pred_bi.values()) if pred_bi else 0
    recall = overlap / sum(ref_bi.values()) if ref_bi else 0

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def rouge_l(predicted, reference):
    """ROUGE-L: longest common subsequence based F1."""
    pred_tokens = predicted.lower().split()
    ref_tokens = reference.lower().split()
    m, n = len(pred_tokens), len(ref_tokens)

    # LCS via DP
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if pred_tokens[i-1] == ref_tokens[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    lcs_len = dp[m][n]
    precision = lcs_len / m if m else 0
    recall = lcs_len / n if n else 0

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# --- LLM-as-Judge ---

def llm_judge(question, answer, criteria="helpfulness, accuracy, completeness"):
    """Use LLM to score an answer 1-5."""
    prompt = (
        f"Rate this answer on a scale of 1-5 for {criteria}.\n\n"
        f"Question: {question}\n"
        f"Answer: {answer}\n\n"
        f"First explain your reasoning in 1-2 sentences, then give the score.\n"
        f"Format: SCORE: X/5"
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a strict evaluator. Be honest and specific."},
                {"role": "user", "content": prompt}
            ],
        )
        text = resp.choices[0].message.content if resp.choices else None
        if not text:
            return None, "Empty response from model"
        match = re.search(r"SCORE:\s*(\d)", text)
        score = int(match.group(1)) if match else None
        return score, text
    except Exception as e:
        return None, str(e)


# --- Eval Runner ---

def run_eval(dataset, generate_fn):
    """Run evaluation over a dataset. Each item: {question, expected, criteria}."""
    results = []
    for item in dataset:
        predicted = generate_fn(item["question"])
        r1 = rouge_1(predicted, item["expected"])
        r2 = rouge_2(predicted, item["expected"])
        rl = rouge_l(predicted, item["expected"])
        em = exact_match(predicted, item["expected"])

        results.append({
            "question": item["question"][:50],
            "exact_match": em,
            "rouge_1": round(r1, 3),
            "rouge_2": round(r2, 3),
            "rouge_l": round(rl, 3),
            "predicted": predicted[:80],
        })
    return results


# --- Golden Dataset ---

EVAL_DATASET = [
    {
        "question": "What is the capital of France?",
        "expected": "The capital of France is Paris.",
        "criteria": "accuracy",
    },
    {
        "question": "What does CPU stand for?",
        "expected": "CPU stands for Central Processing Unit.",
        "criteria": "accuracy",
    },
    {
        "question": "Explain what an API is in one sentence.",
        "expected": "An API is a set of rules and protocols that allows different software applications to communicate with each other.",
        "criteria": "clarity, accuracy",
    },
    {
        "question": "What is Python used for?",
        "expected": "Python is used for web development, data science, machine learning, automation, scripting, and general-purpose programming.",
        "criteria": "completeness",
    },
    {
        "question": "Is the earth flat?",
        "expected": "No, the Earth is not flat. It is an oblate spheroid.",
        "criteria": "accuracy, directness",
    },
]


def generate_answer(question):
    """Simple LLM call to generate an answer."""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Answer concisely in 1-2 sentences."},
                {"role": "user", "content": question},
            ],
        )
        content = resp.choices[0].message.content if resp.choices else None
        return content or "(empty response)"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":

    # --- Part 1: ROUGE scores demo ---
    print("=" * 60)
    print("Part 1: Text Metrics Demo")
    print("=" * 60)

    reference = "Python is a popular programming language used for web development and data science"
    candidates = [
        "Python is a popular programming language used for web development and data science",  # perfect match
        "Python is a programming language for data science and web development",              # paraphrase
        "Java is an enterprise language used for building large scale systems",                # unrelated
    ]

    for i, c in enumerate(candidates):
        print(f"\n  Candidate {i+1}: '{c[:60]}...'")
        print(f"    ROUGE-1: {rouge_1(c, reference):.3f}")
        print(f"    ROUGE-2: {rouge_2(c, reference):.3f}")
        print(f"    ROUGE-L: {rouge_l(c, reference):.3f}")
        print(f"    Exact:   {exact_match(c, reference)}")

    # --- Part 2: Eval runner on golden dataset ---
    print("\n" + "=" * 60)
    print("Part 2: Eval Runner on Golden Dataset")
    print("=" * 60)
    print(f"\nRunning {len(EVAL_DATASET)} eval cases...\n")

    results = run_eval(EVAL_DATASET, generate_answer)
    for r in results:
        print(f"  Q: {r['question']}")
        print(f"    R1={r['rouge_1']} R2={r['rouge_2']} RL={r['rouge_l']} EM={r['exact_match']}")
        print(f"    Got: {r['predicted'][:70]}...")
        print()

    avg_r1 = sum(r["rouge_1"] for r in results) / len(results)
    avg_rl = sum(r["rouge_l"] for r in results) / len(results)
    print(f"  Average ROUGE-1: {avg_r1:.3f}")
    print(f"  Average ROUGE-L: {avg_rl:.3f}")

    # --- Part 3: LLM-as-Judge ---
    print("\n" + "=" * 60)
    print("Part 3: LLM-as-Judge")
    print("=" * 60)

    judge_question = "What is machine learning?"
    judge_answer = "Machine learning is a subset of AI where computers learn patterns from data without being explicitly programmed."

    print(f"\n  Judging: '{judge_answer[:60]}...'")
    score, reasoning = llm_judge(judge_question, judge_answer)
    print(f"  Score: {score}/5")
    print(f"  Reasoning: {reasoning[:150]}...")
