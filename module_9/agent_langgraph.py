import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

load_dotenv()

llm = ChatOpenAI(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Use for any calculations."""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: invalid characters"
    return str(eval(expression))


@tool
def word_count(text: str) -> str:
    """Count the number of words in given text."""
    return str(len(text.split()))


@tool
def reverse_string(text: str) -> str:
    """Reverse the given string and return it."""
    return text[::-1]


tools = [calculator, word_count, reverse_string]
llm_with_tools = llm.bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def call_model(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


tool_node = ToolNode(tools)


def should_continue(state: AgentState):
    last_msg = state["messages"][-1]
    if last_msg.tool_calls:
        return "tools"
    return END


# build the graph
graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")
app = graph.compile()


if __name__ == "__main__":
    msgs = [
        SystemMessage(content="You are a helpful assistant. Use tools when needed."),
        HumanMessage(content="What is (15 * 24) + (30 / 5)?"),
    ]
    result = app.invoke({"messages": msgs})
    print(f"Answer: {result['messages'][-1].content}")

    msgs = [
        SystemMessage(content="You are a helpful assistant. Use tools when needed."),
        HumanMessage(content="Count words in 'the quick brown fox jumps over the lazy dog' and square it"),
    ]
    result = app.invoke({"messages": msgs})
    print(f"Answer: {result['messages'][-1].content}")

    msgs = [
        SystemMessage(content="You are a helpful assistant. Use tools when needed."),
        HumanMessage(content="Reverse the word 'artificial'"),
    ]
    result = app.invoke({"messages": msgs})
    print(f"Answer: {result['messages'][-1].content}")
