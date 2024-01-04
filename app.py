from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# OpenAI client setup (remains the same)
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
with open("Cjcontent.txt", "r", encoding="utf-8") as f:
    custom_data = f.read()
history = [
    {"role": "system", "content": "You are an intelligent chat assistant trained on custom data of a company named cloud June. Provide responses that are consistent with the provided information."},
    {"role": "user", "content": "Hello, introduce yourself to someone opening this program for the first time. Be concise."},
]

@app.route('/')
def index():
    return render_template("base.html")

@app.route("/predict", methods=["POST"])
def predict():
    message = request.json["message"]

    history.append({"role": "user", "content": message})
    completion = client.chat.completions.create(
        model="local-model",
        messages=history,
        temperature=0.7,
        stream=True,
    )

    new_message = {"role": "assistant", "content": ""}
    for chunk in completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
            new_message["content"] += chunk.choices[0].delta.content

    history.append(new_message)
    return jsonify({"answer": new_message["content"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
