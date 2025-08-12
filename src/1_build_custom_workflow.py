# reference: https://langchain-ai.github.io/langgraph/concepts/why-langgraph/

########################################################
############ 1. build a basic chatbot ##################
########################################################

# # create state graph
# from typing import Annotated

# from typing_extensions import TypedDict

# from langgraph.graph import StateGraph, START, END
# from langgraph.graph.message import add_messages


# class State(TypedDict):
#     # Messages have the type "list". The `add_messages` function
#     # in the annotation defines how this state key should be updated
#     # (in this case, it appends messages to the list, rather than overwriting them)
#     messages: Annotated[list, add_messages]


# graph_builder = StateGraph(State)

# # add a node
# from langchain_ollama import ChatOllama

# llm = ChatOllama(
#     model="llama3.2",
#     temperature=0,
# )

# def chatbot(state: State):
#     return {"messages": [llm.invoke(state["messages"])]}

# graph_builder.add_node("chatbot", chatbot)

# # add an entry point
# graph_builder.add_edge(START, "chatbot")

# # add an exit point
# graph_builder.add_edge("chatbot", END)

# # compile the graph
# graph = graph_builder.compile()

# # visualize the graph
# import os
# try:
#     current_path = os.path.dirname(os.path.abspath(__file__))
#     outputFilename = os.path.join(current_path, '..', 'tests', '1_basic_chatbot.png')
#     graph.get_graph().draw_mermaid_png(output_file_path=outputFilename)
#     print(f"Saved graph to {outputFilename}")
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

# # run the chatbot
# def stream_graph_updates(user_input: str):
#     for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
#         for value in event.values():
#             print("Assistant:", value["messages"][-1].content)


# while True:
#     try:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
#         stream_graph_updates(user_input)
#     except:
#         # fallback if input() is not available
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         stream_graph_updates(user_input)
#         break

########################################################
############ 2. add tools ##################
########################################################
# # configure environment
# # reference: Tavily web tool https://www.tavily.com/
# import getpass
# import os
# from dotenv import load_dotenv

# load_dotenv()

# if not os.environ.get("TAVILY_API_KEY"):
#     os.environ["TAVILY_API_KEY"] = os.getenv('TAVILY_API_KEY')

# # define the web search tool
# from langchain_tavily import TavilySearch

# tool = TavilySearch(max_results=2)
# tools = [tool]

# # # test tool
# # results = tool.invoke("What's a 'node' in LangGraph?")
# # import pprint
# # pprint.pprint(results)

# # define the graph
# from typing import Annotated

# from typing_extensions import TypedDict

# from langgraph.graph import StateGraph, START, END
# from langgraph.graph.message import add_messages


# class State(TypedDict):
#     # Messages have the type "list". The `add_messages` function
#     # in the annotation defines how this state key should be updated
#     # (in this case, it appends messages to the list, rather than overwriting them)
#     messages: Annotated[list, add_messages]


# graph_builder = StateGraph(State)

# # add a node
# from langchain_ollama import ChatOllama

# llm = ChatOllama(
#     model="llama3.2",
#     temperature=0,
# )

# llm_with_tools = llm.bind_tools(tools)

# def chatbot(state: State):
#     return {"messages": [llm_with_tools.invoke(state["messages"])]}

# graph_builder.add_node("chatbot", chatbot)

# # create a function to run the tools
# import json

# from langchain_core.messages import ToolMessage


# class BasicToolNode:
#     """A node that runs the tools requested in the last AIMessage."""

#     def __init__(self, tools: list) -> None:
#         self.tools_by_name = {tool.name: tool for tool in tools}

#     def __call__(self, inputs: dict):
#         if messages := inputs.get("messages", []):
#             message = messages[-1]
#         else:
#             raise ValueError("No message found in input")
#         outputs = []
#         for tool_call in message.tool_calls:
#             tool_result = self.tools_by_name[tool_call["name"]].invoke(
#                 tool_call["args"]
#             )
#             outputs.append(
#                 ToolMessage(
#                     content=json.dumps(tool_result),
#                     name=tool_call["name"],
#                     args=tool_call["args"],
#                     tool_call_id=tool_call["id"],
#                 )
#             )
#         return {"messages": outputs}


# tool_node = BasicToolNode(tools=[tool])
# graph_builder.add_node("tools", tool_node)

# # define the conditional edges
# def route_tools(
#     state: State,
# ):
#     """
#     Use in the conditional_edge to route to the ToolNode if the last message
#     has tool calls. Otherwise, route to the end.
#     """
#     if isinstance(state, list):
#         ai_message = state[-1]
#     elif messages := state.get("messages", []):
#         ai_message = messages[-1]
#     else:
#         raise ValueError(f"No messages found in input state to tool_edge: {state}")
#     if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
#         return "tools"
#     return END


# # The `tools_condition` function returns "tools" if the chatbot asks to use a tool, and "END" if
# # it is fine directly responding. This conditional routing defines the main agent loop.
# graph_builder.add_conditional_edges(
#     "chatbot",
#     route_tools,
#     # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
#     # It defaults to the identity function, but if you
#     # want to use a node named something else apart from "tools",
#     # You can update the value of the dictionary to something else
#     # e.g., "tools": "my_tools"
#     {"tools": "tools", END: END},
# )
# # Any time a tool is called, we return to the chatbot to decide the next step
# graph_builder.add_edge("tools", "chatbot")
# graph_builder.add_edge(START, "chatbot")
# graph = graph_builder.compile()

# # visualize the graph
# try:
#     current_path = os.path.dirname(os.path.abspath(__file__))
#     outputFilename = os.path.join(current_path, '..', 'tests', '1_basic_chatbot_with_tools.png')
#     graph.get_graph().draw_mermaid_png(output_file_path=outputFilename)
#     print(f"Saved graph to {outputFilename}")
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

# # run the bot
# import pprint

# def stream_graph_updates(user_input: str):
#     for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
#         event["messages"][-1].pretty_print()
#         for value in event.values():
#             if isinstance(value["messages"][-1].name, str):
#                 contents = "Assistant:" + value["messages"][-1].content + " Jack's tool: " + str(value["messages"][-1].name) + " Jack's tool args: " + str(value["messages"][-1].args) + " Jack's tool call id: " + str(value["messages"][-1].tool_call_id)
#             else:
#                 contents = "Assistant:" + value["messages"][-1].content
#             pprint.pprint(
#                 contents,
#                 indent=4,
#                 compact=True
#             )

# while True:
#     try:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
#         stream_graph_updates(user_input)
#     except:
#         # fallback if input() is not available
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         stream_graph_updates(user_input)
#         break

########################################################
############ 3. add memory ##################
########################################################
from typing import Annotated

from langchain_tavily import TavilySearch
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

import os
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("TAVILY_API_KEY"):
    os.environ["TAVILY_API_KEY"] = os.getenv('TAVILY_API_KEY')

tool = TavilySearch(max_results=2)
tools = [tool]

from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2",
    temperature=0,
)
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")

# create a MemorySaver checkpointer
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()

# compile a graph
graph = graph_builder.compile(checkpointer=memory)

# interact with your chatbot
# Pick a thread to use as the key for this conversation
config = {"configurable": {"thread_id": "1"}}

# Call your chatbot
user_input = "Hi there! My name is Will."

# The config is the **second positional argument** to stream() or invoke()!
events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()

# Ask a follow-up question
user_input = "Remember my name?"

# The config is the **second positional argument** to stream() or invoke()!
events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()

# The only difference is we change the `thread_id` here to "2" instead of "1"
events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    {"configurable": {"thread_id": "2"}},
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()


########################################################
############ 4. add human-in-the-loop controls ##################
########################################################

########################################################
############ 5. customize state ##################
########################################################

########################################################
############ 6. Time travel ##################
########################################################