from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app import config
from app.vectorstore import get_vectorstore

RAG_PROMPT = """You are an assistant for question-answering tasks. Use the following
retrieved context to answer the question. If you cannot answer based on the context, say so
clearly. Cite the source filenames in your answer.

Context:
{context}

Question: {question}"""

llm = ChatOpenAI(
    model=config.OPENROUTER_MODEL,
    api_key=config.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
)

prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
rag_chain = prompt | llm | StrOutputParser()

retriever = get_vectorstore().as_retriever(search_kwargs={"k": config.RETRIEVE_K})


def ask(question: str) -> dict:
    docs = retriever.invoke(question)

    if not docs:
        return {"answer": "No relevant documents found in the knowledge base.", "sources": ""}

    context = "\n\n".join(f"[{d.metadata.get('source', '?')}]\n{d.page_content}" for d in docs)
    sources = ", ".join(sorted({d.metadata.get("source", "?") for d in docs}))

    answer = rag_chain.invoke({"question": question, "context": context})
    return {"answer": answer, "sources": sources}
