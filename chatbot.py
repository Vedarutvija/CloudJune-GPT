from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import mysql.connector

app = Flask(__name__)

# OpenAI client setup (remains the same)
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

# MySQL database connection setup
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Mysql@27#",
    "database": "college",
}

connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()

# Fetch data from the 'webcontent' table in the 'college' database
cursor.execute("SELECT content FROM college.webcontent;")
result = cursor.fetchone()
custom_data = result[0] if result else ""
cursor.fetchall()
# Close the MySQL connection
cursor.close()
connection.close()

history = [
    {"role": "system", "content": "You are an intelligent chat assistant trained on custom data of a company named cloud June. Provide responses that are consistent with the provided information."},
    {"role": "user", "content": f"Here is the information from the website: {custom_data}"},
]

@app.route('/')
def index():
    return render_template("base.html")
@app.route("/predict", methods=["POST"])
def predict():
    message = request.json["message"]

    # Establish MySQL connection and cursor
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    cursor.execute('INSERT INTO conversations (user_query, bot_response) VALUES (%s, %s)', ('user', message))
    connection.commit()

    # Update user's message with the actual user input
    history[-1]["content"] = message

    # Append the user's message to the history
    history.append({"role": "user", "content": message})

    # Make a request to OpenAI for completion
    completion = client.chat.completions.create(
        model="local-model",
        messages=history,
        temperature=0.7,
        stream=True,
    )

    # Process the completion and update history with assistant's response
    new_message = {"role": "assistant", "content": ""}
    for chunk in completion:
        if chunk.choices[0].delta.content:
            new_message["content"] += chunk.choices[0].delta.content

    cursor.execute('INSERT INTO conversations(user_query, bot_response) VALUES (%s, %s)', ('assistant', new_message["content"]))
    connection.commit()

    # Close MySQL connection and cursor
    cursor.close()
    connection.close()

    # Append assistant's response to the history
    history.append(new_message)

    return jsonify({"answer": new_message["content"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
