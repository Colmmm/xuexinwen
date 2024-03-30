import os
import json
import mysql.connector

# MySQL connection configuration
db_config = {
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'database': os.environ.get('MYSQL_DATABASE'),
    'host': 'mysql' # as defined in docker-compose file
}

# Function to establish MySQL connection
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print("Error connecting to MySQL:", err)
        return None

# Function to create tables if not exist
def create_tables(cursor):
    try:
        # Check if tables exist
        cursor.execute("SHOW TABLES LIKE 'articles'")
        articles_table_exists = cursor.fetchone()
        cursor.execute("SHOW TABLES LIKE 'Images'")
        images_table_exists = cursor.fetchone()

        # If tables exist, drop them
        if articles_table_exists and images_table_exists:
            cursor.execute("DROP TABLE articles")
            cursor.execute("DROP TABLE Images")

        # Read schema from file and create tables
        with open('/app/setup.sql', 'r') as file:
            schema = file.read()
            cursor.execute(schema)

    except mysql.connector.Error as err:
        print("Error creating tables:", err)


# Function to insert data into articles table
def insert_article(cursor, article):
    try:
        query = "INSERT INTO articles (id, title, text, url, simplified_title, simplified_text, keywords) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (article['id'], article['title'], article['text'], article['url'],
                                article['simplified_title'], article.get('simplified_text', None),
                                json.dumps(article['dict'])))
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry error code
            print("Skipping insertion of duplicate article:", err)
        elif err.errno == 1406:
            print(f"Article url length of {len(article['url'])} is too long")
        else:
            print("Error inserting article:", err)
    except TypeError as err:
        pass


# Function to insert data into Images table
def insert_images(cursor, article):
    try:
        for image_url in article['images']:
            query = "INSERT INTO Images (article_id, image_url) VALUES (%s, %s)"
            cursor.execute(query, (article['id'], image_url))
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry error code
            print("Skipping insertion of duplicate article:", err)
        else:
            print("Error inserting images:", err)
    except TypeError as err:
        pass


# Main function
def main():
    # Connect to MySQL
    conn = connect_to_mysql()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # Create tables if not exist
        #create_tables(cursor)

        # Read JSON files from the 'articles' directory
        articles_dir = '/app/articles/'
        for filename in os.listdir(articles_dir):
            if filename.endswith('.json'):
                with open(os.path.join(articles_dir, filename), 'r') as file:
                    article_data = json.load(file)

                    # Insert article data into articles table
                    insert_article(cursor, article_data)

                    # Insert image data into Images table
                    insert_images(cursor, article_data)

        # Commit changes
        conn.commit()

    except mysql.connector.Error as err:
        print("Error:", err)
        conn.rollback()  # Rollback changes if any error occurs

    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
