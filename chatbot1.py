from flask import Flask, render_template, request, jsonify
import ollama
import mysql.connector as mysql
import atexit
#from langchain.llms import Ollama
from langchain import HuggingFaceHub
from llama_index import VectorStoreIndex, ServiceContext, SimpleDirectoryReader
from llama_index.vector_stores import ChromaVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from llama_index.storage.storage_context import StorageContext
from langchain.chains import RetrievalQA
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
import gradio as gr
import os
import chromadb

from pathlib import Path


class CustomCallbackHandler(BaseCallbackHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_llm_new_token(self, token: str, **kwargs: any) -> None:
        # Implement here your streaming logic
        print(token, end='', flush=True)




callback_manager=CallbackManager([CustomCallbackHandler(),
                                  StreamingStdOutCallbackHandler()])
HUGGINGFACEHUB_API_TOKEN="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"
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
#ollama = Ollama(base_url="http://localhost:11434", model="mistral", callback_manager=callback_manager)
repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
 
llm = HuggingFaceHub(repo_id=repo_id, model_kwargs={"temperature":1, "max_length":500})
#ading the documents from the disk
documents = SimpleDirectoryReader("./data").load_data()

chroma_client = chromadb.Client()
chroma_collection = chroma_client.create_collection("cloudjune")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Initializing the Large Language Model (LLM) with Ollama
# The request_timeout may need to be adjusted depending on the system's performance capabilities
#llm = Ollama(model="mixtral", request_timeout=120.0)
service_context = ServiceContext.from_defaults(llm=llm, embed_model="local")

# Creating the index, which includes embedding the documents into the vector store
index = VectorStoreIndex.from_documents(documents, service_context=service_context, storage_context=storage_context)
    #result = qachain({"query": question})
    #print("Question:" + question)
    #print("Answer" + result["result"])

query_engine = index.as_query_engine()

app = Flask(__name__)

# OpenAI client setup (remains the same)
#client = OpenAI(base_url="http://localhost:11434", api_key="not-needed")
#iwith open("webcontent.txt", "r", encoding="utf-8") as f:
#    custom_data = f.read()
history = [
    {"role": "system", "content": "You are an intelligent chat assistant trained on custom data of a company named cloud June and should act as their assistant. Provide responses that are soley consistent with the provided information. Be polite and respectful when handling sensitive topics. If you're unsure how to respond, it's better to acknowledge the sensitivity and offer to direct the user to a more appropriate resource."},  # Added guidance for sensitive topics
    {"role": "user", "content": "Hello, introduce yourself to someone opening this program for the first time. Be concise."},
]

# MySQL Database Configuration for Conversations
conversation_db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'uch$xilC2g',
    'database': 'cloudjunebot',
}

conversation_connection = mysql.connect(**conversation_db_config)

@app.route('/')
def index():
    return render_template("base.html")


@app.route("/predict", methods=["POST"])
def predict():
    message = request.json["message"]
    instruction_prompt = "**You are a chat assistant created for a company named CouldJune to answer user questions about the company. Your responses should solely depend on the custom data you are trained about the company only. After every response you should ask the user to share their name and email so that the team can reachout to them. Do it only until they provide their name and email. Please don't truncate the responses, you can generate another message with continuation if needed. Act accordingly:** " + message
    
    # Insert user query into conversations table
    cursor = conversation_connection.cursor()
    cursor.execute('INSERT INTO conversations (user_query, bot_response) VALUES (%s, %s)', ('user', message))
    conversation_connection.commit()

    # Check for potential sensitive topics
    sensitive_topics = ["politics", "religion", "caste", "personal health", "sexual orientation", "race", "abusive words"]  # Customize this list
    if any(topic in message.lower() for topic in sensitive_topics):
        response = "I understand this is a sensitive topic. To ensure I provide the most accurate and respectful information, I'd recommend consulting with a human expert or visiting a reputable resource on this matter"
    else:
        #response = #process_url_and_question("https://cloudjune.com",message)
        response= query_engine.query(instruction_prompt) #qachain({"query": message})
        #response.print_response_stream()
        response=str(response).split('Answer:',1)[1]
        print("Question: "+message)
        print("Answer: "+response)
        cursor.execute('INSERT INTO conversations (user_query, bot_response) VALUES (%s, %s)', ('assistant', response))
        conversation_connection.commit()

        cursor.close()

        #history.append(new_message)
        #response = new_message["content"]

    return jsonify({"answer": response})

@atexit.register
def on_exit():
    conversation_connection.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
