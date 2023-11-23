import json
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

app = Flask(__name__)
app.config.from_object(Config) #loading in config such as FLASK_ENV = "production" or "development"
CORS(app, resources={r"/api/*": {"origins": Config.REACT_APP_URL}})

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", Config.REACT_APP_URL)
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

# Flask endpoint to serve the list of article IDs
@app.route('/api/article_ids', methods=['GET'])
def get_article_ids():
    with open('./articles/articles.json', 'r') as file:
        article_ids = json.load(file)
    return jsonify(article_ids)

# Flask endpoint to serve processed articles
@app.route('/api/articles/<article_id>', methods=['GET'])
def get_processed_article(article_id):
    with open(f"articles/{article_id}.json") as f:
        article = json.load(f)
    return jsonify(article)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
