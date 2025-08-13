# reference: https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/#5-rewrite-question
# setup environment
import os
from dotenv import load_dotenv

load_dotenv()

# create worker agents
# research agent will have access to web crawling tools
from langchain_tavily import TavilySearch

web_search = TavilySearch(max_results=3)

# web_search_results = web_search.invoke("who is the mayor of NYC?")
# print(web_search_results["results"][0]["content"])

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

research_agent_model = ChatOllama(
    model=os.environ["RESEARCH_AGENT_MODEL"],
    temperature=0,
)

research_agent = create_react_agent(
    model=research_agent_model,
    tools=[web_search],
    prompt=(
        "You are a research agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with research-related tasks, DO NOT do any math.\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="research_agent",
)

from langchain_core.messages import convert_to_messages

def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")

# for chunk in research_agent.stream(
#     {"messages": [{"role": "user", "content": "who is the mayor of NYC?"}]}
# ):
#     pretty_print_messages(chunk)

# math agents will have access to simple math tools, e.g. add, multiply, divide, etc.
def add(a: float, b: float):
    """Add two numbers."""
    return a + b


def multiply(a: float, b: float):
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float):
    """Divide two numbers."""
    return a / b

math_agent_model = ChatOllama(
    model=os.environ["MATH_AGENT_MODEL"],
    temperature=0,
)

math_agent = create_react_agent(
    model=math_agent_model,
    tools=[add, multiply, divide],
    prompt=(
        "You are a math agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with math-related tasks\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="math_agent",
)

# for chunk in math_agent.stream(
#     {"messages": [{"role": "user", "content": "what's (3 + 5) x 7"}]}
# ):
#     pretty_print_messages(chunk)


# create supervisor
# from langgraph_supervisor import create_supervisor

# supervisor_model = ChatOllama(
#     model=os.environ["SUPERVISOR_MODEL"],
#     temperature=0,
# )

# supervisor = create_supervisor(
#     model=supervisor_model,
#     agents=[research_agent, math_agent],
#     prompt=(
#         "You are a supervisor managing two agents:\n"
#         "- a research agent. Assign research-related tasks to this agent\n"
#         "- a math agent. Assign math-related tasks to this agent\n"
#         "Assign work to one agent at a time, do not call agents in parallel.\n"
#         "Do not do any work yourself."
#     ),
#     add_handoff_back_messages=True,
#     output_mode="full_history",
# ).compile()


# # visualize the graph
# try:
#     current_path = os.path.dirname(os.path.abspath(__file__))
#     outputFilename = os.path.join(current_path, '..', 'tests', '2_3_agentic_supervisor.png')
#     if not os.path.exists(outputFilename):
#         supervisor.get_graph().draw_mermaid_png(output_file_path=outputFilename)
#         print(f"Saved graph to {outputFilename}")
#     else:
#         print(f"{outputFilename} already exists")
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass


# for chunk in supervisor.stream(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": "find US and New York state GDP in 2024. what % of US GDP was New York state?",
#             }
#         ]
#     },
# ):
#     pretty_print_messages(chunk, last_message=True)

# final_message_history = chunk["supervisor"]["messages"]


# create supervisor from scratch
# setup agent communication between supervisor agent and worker agetns
from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command


def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        return Command(
            goto=agent_name,  
            update={**state, "messages": state["messages"] + [tool_message]},  
            graph=Command.PARENT,  
        )

    return handoff_tool


# Handoffs
assign_to_research_agent = create_handoff_tool(
    agent_name="research_agent",
    description="Assign task to a researcher agent.",
)

assign_to_math_agent = create_handoff_tool(
    agent_name="math_agent",
    description="Assign task to a math agent.",
)

# create supervisor agent
supervisor_model = ChatOllama(
    model=os.environ["SUPERVISOR_MODEL"],
    temperature=0,
).bind_tools([assign_to_research_agent, assign_to_math_agent])

# supervisor_agent = create_react_agent(
#     model=supervisor_model,
#     tools=[assign_to_research_agent, assign_to_math_agent],
#     prompt=(
#         "You are a supervisor managing two agents:\n"
#         "- a research agent. Assign research-related tasks to this agent\n"
#         "- a math agent. Assign math-related tasks to this agent\n"
#         "Assign work to one agent at a time, do not call agents in parallel.\n"
#         "Do not do any work yourself."
#     ),
#     name="supervisor"
# )

# # create multi-agent graph
# from langgraph.graph import END

# # Define the multi-agent supervisor graph
# supervisor = (
#     StateGraph(MessagesState)
#     # NOTE: `destinations` is only needed for visualization and doesn't affect runtime behavior
#     .add_node(supervisor_agent, destinations=("research_agent", "math_agent", END))
#     .add_node(research_agent)
#     .add_node(math_agent)
#     .add_edge(START, "supervisor")
#     # always return back to the supervisor
#     .add_edge("research_agent", "supervisor")
#     .add_edge("math_agent", "supervisor")
#     .compile()
# )

# # visualize the graph
# try:
#     current_path = os.path.dirname(os.path.abspath(__file__))
#     outputFilename = os.path.join(current_path, '..', 'tests', '2_3_customized_agentic_supervisor.png')
#     if not os.path.exists(outputFilename):
#         supervisor.get_graph().draw_mermaid_png(output_file_path=outputFilename)
#         print(f"Saved graph to {outputFilename}")
#     else:
#         print(f"{outputFilename} already exists")
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

# for chunk in supervisor.stream(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": "find US and New York state GDP in 2024. what % of US GDP was New York state?",
#             }
#         ]
#     },
# ):
#     pretty_print_messages(chunk, last_message=True)

# final_message_history = chunk["supervisor"]["messages"]

# for message in final_message_history:
#     message.pretty_print()

# create delegation tasks
from langgraph.types import Send


def create_task_description_handoff_tool(
    *, agent_name: str, description: str | None = None
):
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        # this is populated by the supervisor LLM
        task_description: Annotated[
            str,
            "Description of what the next agent should do, including all of the relevant context.",
        ],
        # these parameters are ignored by the LLM
        state: Annotated[MessagesState, InjectedState],
    ) -> Command:
        task_description_message = {"role": "user", "content": task_description}
        agent_input = {**state, "messages": [task_description_message]}
        return Command(
            goto=[Send(agent_name, agent_input)],
            graph=Command.PARENT,
        )

    return handoff_tool


assign_to_research_agent_with_description = create_task_description_handoff_tool(
    agent_name="research_agent",
    description="Assign task to a researcher agent.",
)

assign_to_math_agent_with_description = create_task_description_handoff_tool(
    agent_name="math_agent",
    description="Assign task to a math agent.",
)

supervisor_agent_with_description = create_react_agent(
    model=supervisor_model,
    tools=[
        assign_to_research_agent_with_description,
        assign_to_math_agent_with_description,
    ],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a research agent. Assign research-related tasks to this assistant\n"
        "- a math agent. Assign math-related tasks to this assistant\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    name="supervisor",
)

supervisor_with_description = (
    StateGraph(MessagesState)
    .add_node(
        supervisor_agent_with_description, destinations=("research_agent", "math_agent")
    )
    .add_node(research_agent)
    .add_node(math_agent)
    .add_edge(START, "supervisor")
    .add_edge("research_agent", "supervisor")
    .add_edge("math_agent", "supervisor")
    .compile()
)

for chunk in supervisor_with_description.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "find US and New York state GDP in 2024. what % of US GDP was New York state?",
            }
        ]
    },
    subgraphs=True,
):
    pretty_print_messages(chunk, last_message=True)
