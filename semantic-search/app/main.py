from sentence_transformers import SentenceTransformer
import numpy as np
import json

model = SentenceTransformer("all-MiniLM-L6-v2")

corpus = [
    "The cat sat on the mat.",
    "Dogs are loyal and friendly companions.",
    "Python is a popular programming language.",
    "Kittens love to play with yarn.",
    "I am yosuva"
]

# converting to vector embeddings
doc_embeddings = model.encode(corpus, normalize_embeddings=True) 
print(doc_embeddings.shape)

# saving embeddings & original data
np.save("doc_embeddings.npy", doc_embeddings)
with open("corpus.json", "w") as f:
    json.dump(corpus, f)

# loadig them
doc_embeddings = np.load("doc_embeddings.npy")
corpus = json.load(open("corpus.json"))

query = "which is friendly pet"
q = model.encode([query], normalize_embeddings=True)[0] 

scores = doc_embeddings @ q      # matrix multiplication
top_k = np.argsort(-scores)[:5]    # finding highest

for i in top_k:
    print(f"{scores[i]:.3f}  {corpus[i]}")