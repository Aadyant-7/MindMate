from multiprocessing import Manager, Process
import traceback
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Config
ENDPOINT = "https://models.github.ai/inference"
MODEL = "openai/gpt-4.1"
TOKEN = "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"

# Initialize client
client = ChatCompletionsClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(TOKEN),
)

# System prompt
chat_history = [
    SystemMessage(content=(
        "You are MindMate, a compassionate and understanding mental health assistant. "
        "You listen carefully and respond with empathy, support, and helpful advice. "
        "Give short and concise message but with deepness, use bullet points like 1. 2. etc to show any steps. "
        "Use proper formatting. Do not give very long answers. Use emojis to keep the tone soothing. "
        "Do not use '*' symbols to bold text. In my text box, it won't bold the text so don't use asterisks at all in the response. "
        "For answers with bullet points use this format: Bla Bla Bla:\n"
        "1. Bla  \n2. Bla  \n3. Bla\n\nBla."
    ))
]

# Worker
def _bot_request_worker(user_input, return_dict):
    try:
        chat_history.append(UserMessage(content=user_input))
        response = client.complete(
            messages=chat_history,
            temperature=0.7,
            top_p=0.9,
            max_tokens=1024,
            model=MODEL,
        )
        bot_reply = response.choices[0].message.content.strip()
        chat_history.append(SystemMessage(content=bot_reply))
        return_dict["result"] = bot_reply
    except Exception as e:
        return_dict["error"] = str(e)
        return_dict["trace"] = traceback.format_exc()

# Interface
def get_bot_response(user_input: str, timeout: int = 10) -> str:
    manager = Manager()
    return_dict = manager.dict()
    p = Process(target=_bot_request_worker, args=(user_input, return_dict))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        raise TimeoutError("Request timed out.")
    if "error" in return_dict:
        raise RuntimeError(f"Bot Error: {return_dict['error']}\n{return_dict['trace']}")
    
    return return_dict.get("result", "")