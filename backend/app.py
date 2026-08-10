from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Git-Driven Deployment Engine is running!"

if __name__ == "__main__":
    app.run(debug=True)