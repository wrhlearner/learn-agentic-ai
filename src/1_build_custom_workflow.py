# reference: https://langchain-ai.github.io/langgraph/concepts/why-langgraph/

########################################################
############ 1. build a basic chatbot ##################
########################################################

# create state graph
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

# add a node
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2",
    temperature=0,
)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

# add an entry point
graph_builder.add_edge(START, "chatbot")

# add an exit point
graph_builder.add_edge("chatbot", END)

# compile the graph
graph = graph_builder.compile()

# visualize the graph
import os
try:
    current_path = os.getcwd()
    outputFilename = os.path.join(current_path, 'tests', '1_basic_chatbot.png')
    graph.get_graph().draw_mermaid_png(output_file_path=outputFilename)
    print(f"Saved graph to {outputFilename}")
except Exception:
    # This requires some extra dependencies and is optional
    pass

# run the chatbot
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break

########################################################
############ 2. add tools ##################
########################################################

########################################################
############ 3. add memory ##################
########################################################

########################################################
############ 4. add human-in-the-loop controls ##################
########################################################

########################################################
############ 5. customize state ##################
########################################################

########################################################
############ 6. Time travel ##################
########################################################