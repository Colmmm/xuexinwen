import os
from typing import List, Optional, Dict
from datetime import datetime
import mysql.connector
from mysql.connector import pooling

from article import Article, ArticleSection

class DatabaseManager:
    """Manages MySQL database operations for articles."""
    
    def __init__(self):
        """Initialize database connection pool."""
        dbconfig = {
            "host": "mysql",  # Docker service name
            "database": os.environ['MYSQL_DATABASE'],
            "user": os.environ['MYSQL_USER'],
            "password": os.environ['MYSQL_PASSWORD'],
            "charset": "utf8mb4",
            "use_unicode": True,
            "collation": "utf8mb4_unicode_ci"
        }
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="article_pool",
            pool_size=5,
            **dbconfig
        )
    
    def add_article(self, article: Article) -> None:
        """
        Add a new article to the database.
        
        Args:
            article: Article to add
        """
        conn = self.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Start transaction
            conn.start_transaction()
            
            # Insert main article data
            cursor.execute("""
                INSERT INTO articles (
                    article_id, url, date, source,
                    mandarin_title, english_title
                ) VALUES (
                    %(article_id)s, %(url)s, %(date)s, %(source)s,
                    %(mandarin_title)s, %(english_title)s
                ) ON DUPLICATE KEY UPDATE
                    url=VALUES(url),
                    date=VALUES(date),
                    source=VALUES(source),
                    mandarin_title=VALUES(mandarin_title),
                    english_title=VALUES(english_title)
            """, {
                'article_id': article.article_id,
                'url': article.url,
                'date': article.date,
                'source': article.source,
                'mandarin_title': article.mandarin_title,
                'english_title': article.english_title
            })
            
            # Clear existing authors and insert new ones
            cursor.execute("""
                DELETE FROM authors WHERE article_id = %s
            """, (article.article_id,))
            
            if article.authors:
                cursor.executemany("""
                    INSERT INTO authors (article_id, author)
                    VALUES (%s, %s)
                """, [(article.article_id, author) for author in article.authors])
            
            # Clear existing sections and graded versions
            cursor.execute("""
                DELETE s FROM sections s
                WHERE s.article_id = %s
            """, (article.article_id,))
            
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
                
                # Insert graded versions if they exist
                if section.graded:
                    cursor.executemany("""
                        INSERT INTO graded_sections (
                            section_id, cefr_level, content
                        ) VALUES (%s, %s, %s)
                    """, [
                        (section_id, level, content)
                        for level, content in section.graded.items()
                    ])
            
            # Commit transaction
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
            
        finally:
            cursor.close()
            conn.close()
    
    def get_article(self, article_id: str) -> Optional[Article]:
        """
        Retrieve an article from the database.
        
        Args:
            article_id: ID of the article to retrieve
            
        Returns:
            Article if found, None otherwise
        """
        conn = self.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
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
            
            # Create and return Article instance
            return Article(
                article_id=article_data['article_id'],
                url=article_data['url'],
                date=article_data['date'],
                source=article_data['source'],
                authors=authors,
                mandarin_title=article_data['mandarin_title'],
                english_title=article_data['english_title'],
                sections=sections
            )
            
        finally:
            cursor.close()
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
        conn = self.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
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
            cursor.close()
            conn.close()
