import os
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import time
import json

from article import Article, ArticleSection

class DatabaseManager:
    """Manages MySQL database operations for articles."""
    
    def __init__(self, max_retries=5, retry_delay=5):
        """Initialize database connection."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dbconfig = {
            "host": "mysql",  # Docker service name
            "port": 3306,     # MySQL port
            "database": os.environ['MYSQL_DATABASE'],
            "user": os.environ['MYSQL_USER'],
            "password": os.environ['MYSQL_PASSWORD'],
            "charset": "utf8mb4",
            "use_unicode": True,
            "collation": "utf8mb4_unicode_ci",
            "connect_timeout": 60,  # Increased connection timeout
            "raise_on_warnings": True,
            "allow_local_infile": True
        }
        self._test_connection()
    
    def _test_connection(self):
        """Test the database connection."""
        print(f"Attempting to connect to MySQL at {self.dbconfig['host']}:{self.dbconfig['port']}")
        print(f"Database: {self.dbconfig['database']}")
        print(f"User: {self.dbconfig['user']}")
        
        retries = 0
        while retries < self.max_retries:
            try:
                conn = mysql.connector.connect(**self.dbconfig)
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                print(f"Connected to MySQL version: {version[0]}")
                
                # Set character set
                cursor.execute("SET NAMES utf8mb4")
                conn.commit()
                cursor.execute("SET CHARACTER SET utf8mb4")
                conn.commit()
                cursor.execute("SET character_set_connection=utf8mb4")
                conn.commit()
                
                cursor.close()
                conn.close()
                return
            except Error as e:
                retries += 1
                print(f"Connection attempt {retries} failed: {str(e)}")
                if retries < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed to connect after {self.max_retries} attempts")
    
    def _get_connection(self):
        """Get a new database connection with retries."""
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                conn = mysql.connector.connect(**self.dbconfig)
                cursor = conn.cursor(dictionary=True)
                
                # Set character set for each connection
                cursor.execute("SET NAMES utf8mb4")
                conn.commit()
                cursor.execute("SET CHARACTER SET utf8mb4")
                conn.commit()
                cursor.execute("SET character_set_connection=utf8mb4")
                conn.commit()
                
                return conn, cursor
            except Error as e:
                last_error = e
                retries += 1
                if retries == self.max_retries:
                    print(f"Final connection error: {str(e)}")
                    raise Exception(f"Failed to connect to MySQL after {self.max_retries} attempts: {str(e)}")
                print(f"Failed to get MySQL connection (attempt {retries}/{self.max_retries}). Error: {str(e)}")
                print(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

    def check_article_status(self, article_id: str) -> Tuple[bool, bool]:
        """
        Check if an article exists and has been processed.
        
        Args:
            article_id: ID of the article to check
            
        Returns:
            Tuple[bool, bool]: (exists, processed)
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM articles WHERE article_id = %s) > 0 as article_exists,
                    (SELECT COUNT(*) FROM articles WHERE article_id = %s AND processed = TRUE) > 0 as is_processed
            """, (article_id, article_id))
            result = cursor.fetchone()
            return bool(result['article_exists']), bool(result['is_processed'])
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def mark_article_processed(self, article_id: str) -> None:
        """
        Mark an article as processed.
        
        Args:
            article_id: ID of the article to mark as processed
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            cursor.execute("""
                UPDATE articles SET processed = TRUE
                WHERE article_id = %s
            """, (article_id,))
            conn.commit()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def add_article(self, article: Article, processed: bool = False) -> None:
        """
        Add a new article to the database.
        
        Args:
            article: Article to add
            processed: Whether the article has been processed
        """
        print(f"\nAttempting to add article {article.article_id} to database")
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            
            # Start transaction
            conn.start_transaction()
            
            # Insert main article data
            print("Inserting article data...")
            cursor.execute("""
                INSERT INTO articles (
                    article_id, url, date, source,
                    mandarin_title, english_title, image_url, metadata, processed
                ) VALUES (
                    %(article_id)s, %(url)s, %(date)s, %(source)s,
                    %(mandarin_title)s, %(english_title)s, %(image_url)s, %(metadata)s, %(processed)s
                ) AS new_article
                ON DUPLICATE KEY UPDATE
                    url=new_article.url,
                    date=new_article.date,
                    source=new_article.source,
                    mandarin_title=new_article.mandarin_title,
                    english_title=new_article.english_title,
                    image_url=new_article.image_url,
                    metadata=new_article.metadata,
                    processed=new_article.processed
            """, {
                'article_id': article.article_id,
                'url': article.url,
                'date': article.date,
                'source': article.source,
                'mandarin_title': article.mandarin_title,
                'english_title': article.english_title,
                'image_url': article.image_url,
                'metadata': json.dumps(article.metadata) if article.metadata else None,
                'processed': processed
            })
            conn.commit()
            
            # Clear existing authors and insert new ones
            print("Updating authors...")
            cursor.execute("""
                DELETE FROM authors WHERE article_id = %s
            """, (article.article_id,))
            conn.commit()
            
            if article.authors:
                for author in article.authors:
                    cursor.execute("""
                        INSERT INTO authors (article_id, author)
                        VALUES (%s, %s)
                    """, (article.article_id, author))
                conn.commit()
            
            # Clear existing sections and graded versions
            print("Updating sections...")
            cursor.execute("""
                DELETE s FROM sections s
                WHERE s.article_id = %s
            """, (article.article_id,))
            conn.commit()
            
            # Insert new sections with their graded versions
            for position, section in enumerate(article.sections):
                cursor.execute("""
                    INSERT INTO sections (
                        article_id, position, mandarin, english
                    ) VALUES (
                        %(article_id)s, %(position)s, %(mandarin)s, %(english)s
                    )
                """, {
                    'article_id': article.article_id,
                    'position': position,
                    'mandarin': section.mandarin,
                    'english': section.english
                })
                section_id = cursor.lastrowid
                conn.commit()
                
                # Insert graded versions if they exist
                if section.graded:
                    for level, content in section.graded.items():
                        cursor.execute("""
                            INSERT INTO graded_sections (
                                section_id, cefr_level, content
                            ) VALUES (%s, %s, %s)
                        """, (section_id, level, content))
                        conn.commit()
            
            print(f"Successfully saved article {article.article_id} to database")
            
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Error saving article to database: {str(e)}")
            raise e
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_article(self, article_id: str) -> Optional[Article]:
        """
        Retrieve an article from the database.
        
        Args:
            article_id: ID of the article to retrieve
            
        Returns:
            Article if found, None otherwise
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            
            # Get main article data
            cursor.execute("""
                SELECT * FROM articles WHERE article_id = %s
            """, (article_id,))
            article_data = cursor.fetchone()
            
            if not article_data:
                return None
            
            # Get authors
            cursor.execute("""
                SELECT author FROM authors WHERE article_id = %s
            """, (article_id,))
            authors = [row['author'] for row in cursor.fetchall()]
            
            # Get sections with their graded versions
            cursor.execute("""
                SELECT s.section_id, s.mandarin, s.english,
                       g.cefr_level, g.content as graded_content
                FROM sections s
                LEFT JOIN graded_sections g ON s.section_id = g.section_id
                WHERE s.article_id = %s
                ORDER BY s.position
            """, (article_id,))
            
            # Group sections and their graded versions
            sections = []
            current_section = None
            current_graded = {}
            
            for row in cursor.fetchall():
                if not current_section or current_section['section_id'] != row['section_id']:
                    if current_section:
                        sections.append(ArticleSection(
                            mandarin=current_section['mandarin'],
                            english=current_section['english'],
                            graded=current_graded if current_graded else None
                        ))
                        current_graded = {}
                    
                    current_section = row
                
                if row['cefr_level']:
                    current_graded[row['cefr_level']] = row['graded_content']
            
            # Add last section
            if current_section:
                sections.append(ArticleSection(
                    mandarin=current_section['mandarin'],
                    english=current_section['english'],
                    graded=current_graded if current_graded else None
                ))
            
            # Parse metadata from JSON if it exists
            metadata = json.loads(article_data['metadata']) if article_data['metadata'] else None
            
            # Create and return Article instance
            return Article(
                article_id=article_data['article_id'],
                url=article_data['url'],
                date=article_data['date'],
                source=article_data['source'],
                authors=authors,
                mandarin_title=article_data['mandarin_title'],
                english_title=article_data['english_title'],
                sections=sections,
                image_url=article_data['image_url'],
                metadata=metadata
            )
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_articles(self, 
                    source: Optional[str] = None,
                    limit: int = 10,
                    offset: int = 0) -> List[Article]:
        """
        Retrieve multiple articles with optional filtering.
        
        Args:
            source: Optional source to filter by
            limit: Maximum number of articles to return
            offset: Number of articles to skip
            
        Returns:
            List of articles matching criteria
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            
            # Build query based on filters
            query = "SELECT article_id FROM articles"
            params = []
            
            if source:
                query += " WHERE source = %s"
                params.append(source)
            
            query += " ORDER BY date DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            article_ids = [row['article_id'] for row in cursor.fetchall()]
            
            # Fetch full articles
            return [
                self.get_article(article_id)
                for article_id in article_ids
                if article_id
            ]
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
