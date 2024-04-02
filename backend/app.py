import json
from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": Config.REACT_APP_URL}})

# Establish connection to MySQL database
db_config = {
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'database': os.environ.get('MYSQL_DATABASE'),
    'host': 'mysql' # as defined in docker-compose file
}

def connect_to_mysql():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print("Error connecting to MySQL:", err)
        return None

# Flask endpoint to serve the list of article IDs from MySQL database
@app.route('/api/article_ids', methods=['GET'])
def get_article_ids():
    conn = connect_to_mysql()
    if conn is None:
        return jsonify({'error': 'Failed to connect to database'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM articles")
        article_ids = [row['id'] for row in cursor.fetchall()]
        return jsonify(article_ids)
    except mysql.connector.Error as err:
        print("Error fetching article IDs:", err)
        return jsonify({'error': 'Failed to fetch article IDs'}), 500
    finally:
        cursor.close()
        conn.close()

# Flask endpoint to serve processed articles from MySQL database
@app.route('/api/articles/<article_id>', methods=['GET'])
def get_processed_article(article_id):
    conn = connect_to_mysql()
    if conn is None:
        return jsonify({'error': 'Failed to connect to database'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
        article = cursor.fetchone()
        # Fetch images associated with the article
        cursor.execute("SELECT image_url FROM Images WHERE article_id = %s", (article_id,))
        images = [row['image_url'] for row in cursor.fetchall()]
        article['images'] = images
        return jsonify(article)
    except mysql.connector.Error as err:
        print("Error fetching article:", err)
        return jsonify({'error': 'Failed to fetch article'}), 500
    finally:
        cursor.close()
        conn.close()

# Enable CORS for all routes
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", Config.REACT_APP_URL)
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
