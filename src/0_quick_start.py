# reference: 
# langgraph chatollama https://python.langchain.com/docs/integrations/chat/ollama/

from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2",
    temperature=0,
)

messages = [
    (
        "system",
        "You are a helpful assistant that can answer questions and help with tasks."
    ),
    (
        "human",
        "What is the capital of France?"
    ),
]

ai_msg = llm.invoke(messages)
print(ai_msg)

