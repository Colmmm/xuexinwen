from flask import Flask, jsonify
from gnews import GNews

app = Flask(__name__)

# Sample endpoint to return news data
@app.route('/api/news', methods=['GET'])
def get_news():
    google_news = GNews(country='TW', language='zh-Hant')
    news_data = google_news.get_news('英超')
    return jsonify(news_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
