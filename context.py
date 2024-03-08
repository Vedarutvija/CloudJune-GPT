import re
from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
import atexit
from langchain_community.llms import HuggingFaceHub
from llama_index import VectorStoreIndex, ServiceContext, SimpleDirectoryReader
from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
import os
import chromadb

class CustomCallbackHandler(BaseCallbackHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_llm_new_token(self, token: str, **kwargs: any) -> None:
        # Implement here your streaming logic
        print(token, end='', flush=True)

callback_manager = CallbackManager(
    [CustomCallbackHandler(), StreamingStdOutCallbackHandler()]
)
HUGGINGFACEHUB_API_TOKEN = "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"
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"

llm = HuggingFaceHub(repo_id=repo_id, model_kwargs={"temperature": 0.7, "max_new_tokens": 512})

# Adding the documents from the disk
documents = SimpleDirectoryReader("./data").load_data()

chroma_client = chromadb.Client()
chroma_collection = chroma_client.create_collection("cloudjune")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
service_context = ServiceContext.from_defaults(llm=llm, embed_model="local")
index = VectorStoreIndex.from_documents(documents, service_context=service_context, storage_context=storage_context)
query_engine = index.as_query_engine()

app = Flask(__name__)

# Configure email settings
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'rutvija27@gmail.com'  # Your Gmail username
app.config['MAIL_PASSWORD'] = 'yrofkfvvsdbjhzfr'  # Your Gmail password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# Initialize conversation history with instruction prompt
conversation_history = [
    "You are a pro conversational chat assistant created for a company named CouldJune, you are pro at understanding context and delivers meaningful responses. Your responses should solely depend on the custom data you are trained about the company. After every response you should ask the user to share their name and email so that the team can reach out to them. Do it only until they provide their name and email. Please don't truncate the responses, you can generate another message with continuation if needed. Act accordingly:"
]

def send_email(user_message, bot_response):
    msg = Message('Conversation History', sender='rutvija27@gmail.com', recipients=['j.vedarutvija19@ifheindia.org'])
    msg.body = f"User Message: {user_message}\nBot Response: {bot_response}"
    mail.send(msg)

@app.route("/")
def index():
    return render_template("base.html")

@app.route("/predict", methods=["POST"])
def predict():
    global conversation_history

    message = request.json["message"]
    
    # Append user's message to the conversation history
    conversation_history.append(message)

    # Use the entire conversation history as context for generating responses
    context = " ".join(conversation_history)
    response = query_engine.query(context)  
    response = str(response).split("Answer:", 1)[1]
    
    # Update conversation history with the assistant's response
    conversation_history.append(response)
    context = " ".join(conversation_history)
    print("Question:", message)
    print("Answer:", response)

    # Check if the user message contains an email address
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails_found = re.findall(email_pattern, message)
    
    # If an email address is found, send an email
    if emails_found:
        send_email(message, response)

    return jsonify({"answer": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
