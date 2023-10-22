import json
from flask import Flask, jsonify

app = Flask(__name__)

# Flask endpoint to serve processed articles
@app.route('/api/articles/<article_id>', methods=['GET'])
def get_processed_article(article_id):
    with open(f"articles/{article_id}.json") as f:
        article = json.load(f)
    return jsonify(article)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
