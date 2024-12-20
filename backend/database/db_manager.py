import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import time
import json

from ..article.article import Article
from ..utils.logger_config import setup_logger

logger = setup_logger(__name__)

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
            "connect_timeout": 60,
            "raise_on_warnings": True
        }
        self._test_connection()
    
    def _test_connection(self):
        """Test the database connection."""
        logger.info(f"Attempting to connect to MySQL at {self.dbconfig['host']}:{self.dbconfig['port']}")
        logger.info(f"Database: {self.dbconfig['database']}")
        logger.info(f"User: {self.dbconfig['user']}")
        
        retries = 0
        while retries < self.max_retries:
            try:
                conn = mysql.connector.connect(**self.dbconfig)
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                logger.info(f"Connected to MySQL version: {version[0]}")
                
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
                logger.error(f"Connection attempt {retries} failed: {str(e)}")
                if retries < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
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
                    logger.error(f"Final connection error: {str(e)}")
                    raise Exception(f"Failed to connect to MySQL after {self.max_retries} attempts: {str(e)}")
                logger.error(f"Failed to get MySQL connection (attempt {retries}/{self.max_retries}). Error: {str(e)}")
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

    def check_article_status(self, article_id: str) -> Tuple[bool, bool]:
        """
        Check if an article exists and has been processed.
        
        Args:
            article_id: ID of the article to check
            
        Returns:
            Tuple[bool, bool]: (exists, processed)
        """
        logger.info(f"Checking article {article_id} if it exists and has been processed.")
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
        except Error as e:
            logger.error(f"Error checking article status: {str(e)}")
            raise e
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
        logger.info(f"Marking article {article_id} as processed.")
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            cursor.execute("""
                UPDATE articles SET processed = TRUE
                WHERE article_id = %s
            """, (article_id,))
            conn.commit()
        except Error as e:
            logger.error(f"Error marking article as processed: {str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def add_article(self, article: Article, processed: bool = False) -> None:
        """
        Add or update an article and its related data.
        
        Args:
            article: Article to add/update
            processed: Whether the article has been processed
        """
        logger.info(f"Adding/updating article {article.article_id}")
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            conn.start_transaction()
            
            # Insert/update main article data
            cursor.execute("""
                INSERT INTO articles (
                    article_id, url, date, source, authors,
                    mandarin_title, english_title,
                    mandarin_content, english_content,
                    section_indices, image_url, metadata,
                    processed
                ) VALUES (
                    %(article_id)s, %(url)s, %(date)s, %(source)s, %(authors)s,
                    %(mandarin_title)s, %(english_title)s,
                    %(mandarin_content)s, %(english_content)s,
                    %(section_indices)s, %(image_url)s, %(metadata)s,
                    %(processed)s
                ) AS new_article
                ON DUPLICATE KEY UPDATE
                    url=new_article.url,
                    date=new_article.date,
                    source=new_article.source,
                    authors=new_article.authors,
                    mandarin_title=new_article.mandarin_title,
                    english_title=new_article.english_title,
                    mandarin_content=new_article.mandarin_content,
                    english_content=new_article.english_content,
                    section_indices=new_article.section_indices,
                    image_url=new_article.image_url,
                    metadata=new_article.metadata,
                    processed=new_article.processed
            """, {
                'article_id': article.article_id,
                'url': article.url,
                'date': article.date,
                'source': article.source,
                'authors': json.dumps(article.authors),
                'mandarin_title': article.mandarin_title,
                'english_title': article.english_title,
                'mandarin_content': article.mandarin_content,
                'english_content': article.english_content,
                'section_indices': json.dumps(article.section_indices),
                'image_url': article.image_url,
                'metadata': json.dumps(article.metadata) if article.metadata else None,
                'processed': processed
            })
            
            conn.commit()
            logger.info(f"Successfully saved article {article.article_id}")
            
        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error saving article: {str(e)}", exc_info=True)
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def save_processing_results(self, article_id: str,
                              entities: Dict[str, Dict[str, str]],
                              word_levels: Dict[str, List[str]],
                              graded_content: Dict[str, str]) -> None:
        """
        Save article processing results and mark article as processed.
        
        Args:
            article_id: ID of the processed article
            entities: Dictionary of entity types to {word: definition} mappings
            word_levels: Dictionary of CEFR levels to word lists
            graded_content: Dictionary of CEFR levels to simplified content
        """
        logger.info(f"Saving processing results for article {article_id}")
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            conn.start_transaction()
            
            # Clear existing results
            cursor.execute("DELETE FROM entities WHERE article_id = %s", (article_id,))
            cursor.execute("DELETE FROM word_levels WHERE article_id = %s", (article_id,))
            cursor.execute("DELETE FROM graded_content WHERE article_id = %s", (article_id,))
            
            # Save entities
            for entity_type, entities_dict in entities.items():
                for word, definition in entities_dict.items():
                    cursor.execute("""
                        INSERT INTO entities (
                            article_id, entity_text, entity_type, english_definition
                        ) VALUES (%s, %s, %s, %s)
                    """, (article_id, word, entity_type, definition))
            
            # Save word levels
            for level, words in word_levels.items():
                for word in words:
                    cursor.execute("""
                        INSERT INTO word_levels (
                            article_id, word, cefr_level
                        ) VALUES (%s, %s, %s)
                    """, (article_id, word, level))
            
            # Save graded content
            for level, content in graded_content.items():
                cursor.execute("""
                    INSERT INTO graded_content (
                        article_id, cefr_level, content
                    ) VALUES (%s, %s, %s)
                """, (article_id, level, content))
            
            # Mark article as processed
            cursor.execute("""
                UPDATE articles SET processed = TRUE
                WHERE article_id = %s
            """, (article_id,))
            
            conn.commit()
            logger.info(f"Successfully saved processing results for article {article_id}")
            
        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error saving processing results: {str(e)}", exc_info=True)
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_article(self, article_id: str) -> Optional[Article]:
        """
        Retrieve an article and its related data.
        
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
                logger.warning(f"Article {article_id} not found")
                return None
            
            # Get graded content
            cursor.execute("""
                SELECT cefr_level, content
                FROM graded_content
                WHERE article_id = %s
            """, (article_id,))
            graded_content = {
                row['cefr_level']: row['content']
                for row in cursor.fetchall()
            }
            
            # Create Article instance
            return Article(
                article_id=article_data['article_id'],
                url=article_data['url'],
                date=article_data['date'],
                source=article_data['source'],
                authors=json.loads(article_data['authors']),
                mandarin_title=article_data['mandarin_title'],
                english_title=article_data['english_title'],
                mandarin_content=article_data['mandarin_content'],
                english_content=article_data['english_content'],
                section_indices=json.loads(article_data['section_indices']),
                image_url=article_data['image_url'],
                graded_content=graded_content if graded_content else None,
                metadata=json.loads(article_data['metadata']) if article_data['metadata'] else None
            )
            
        except Error as e:
            logger.error(f"Error retrieving article: {str(e)}", exc_info=True)
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_articles(self, source: Optional[str] = None,
                    limit: int = 10, offset: int = 0) -> List[Article]:
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
            articles = [
                self.get_article(article_id)
                for article_id in article_ids
                if article_id
            ]
            
            logger.info(f"Retrieved {len(articles)} articles")
            return articles
            
        except Error as e:
            logger.error(f"Error retrieving articles: {str(e)}", exc_info=True)
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_processing_results(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve processing results for an article.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Dictionary containing entities, word levels, and graded content
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = self._get_connection()
            
            # Get entities
            cursor.execute("""
                SELECT entity_text, entity_type, english_definition
                FROM entities WHERE article_id = %s
            """, (article_id,))
            entities = {}
            for row in cursor.fetchall():
                entity_type = row['entity_type']
                if entity_type not in entities:
                    entities[entity_type] = {}
                entities[entity_type][row['entity_text']] = row['english_definition']
            
            # Get word levels
            cursor.execute("""
                SELECT word, cefr_level
                FROM word_levels WHERE article_id = %s
            """, (article_id,))
            word_levels = {}
            for row in cursor.fetchall():
                level = row['cefr_level']
                if level not in word_levels:
                    word_levels[level] = []
                word_levels[level].append(row['word'])
            
            # Get graded content
            cursor.execute("""
                SELECT cefr_level, content
                FROM graded_content WHERE article_id = %s
            """, (article_id,))
            graded_content = {
                row['cefr_level']: row['content']
                for row in cursor.fetchall()
            }
            
            return {
                'entities': entities,
                'word_levels': word_levels,
                'graded_content': graded_content
            }
            
        except Error as e:
            logger.error(f"Error retrieving processing results: {str(e)}", exc_info=True)
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
