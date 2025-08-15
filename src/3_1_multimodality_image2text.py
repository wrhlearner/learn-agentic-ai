# reference: https://python.langchain.com/docs/integrations/chat/ollama/#multi-modal
import base64
from io import BytesIO

# from IPython.display import HTML, display
from PIL import Image


def convert_to_base64(pil_image):
    """
    Convert PIL images to Base64 encoded strings

    :param pil_image: PIL image
    :return: Re-sized Base64 string
    """

    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")  # You can change the format if needed
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


# def plt_img_base64(img_base64):
#     """
#     Disply base64 encoded string as image

#     :param img_base64:  Base64 string
#     """
#     # Create an HTML img tag with the base64 string as the source
#     image_html = f'<img src="data:image/jpeg;base64,{img_base64}" />'
#     # Display the image by rendering the HTML
#     display(HTML(image_html))


file_path = r"F:\learn-agentic-ai\data\example_image.jpg"
pil_image = Image.open(file_path)

image_b64 = convert_to_base64(pil_image)
# plt_img_base64(image_b64)

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

load_dotenv()

llm = ChatOllama(
    model=os.environ["VISION_MODEL"], 
    temperature=0
)


def prompt_func(data):
    text = data["text"]
    image = data["image"]

    image_part = {
        "type": "image_url",
        "image_url": f"data:image/jpeg;base64,{image}",
    }

    content_parts = []

    text_part = {"type": "text", "text": text}

    content_parts.append(image_part)
    content_parts.append(text_part)

    return [HumanMessage(content=content_parts)]


query = {"text": "What is in this image?", "image": image_b64}

messages = prompt_func(query)

ai_msg = llm.invoke(messages)
ai_msg.pretty_print()

