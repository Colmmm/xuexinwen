-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS graded_sections;
DROP TABLE IF EXISTS sections;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS articles;

-- Create articles table
CREATE TABLE articles (
    article_id VARCHAR(16) PRIMARY KEY,
    url VARCHAR(512) UNIQUE NOT NULL,
    date TIMESTAMP NOT NULL,
    source VARCHAR(32) NOT NULL,
    mandarin_title TEXT NOT NULL,
    english_title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create authors table
CREATE TABLE authors (
    article_id VARCHAR(16),
    author VARCHAR(255),
    PRIMARY KEY (article_id, author),
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create sections table
CREATE TABLE sections (
    section_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    article_id VARCHAR(16),
    position INT NOT NULL,
    mandarin TEXT NOT NULL,
    english TEXT NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
        ON DELETE CASCADE,
    UNIQUE (article_id, position)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create graded_sections table
CREATE TABLE graded_sections (
    section_id BIGINT,
    cefr_level ENUM('A1', 'A2', 'B1', 'B2'),
    content TEXT NOT NULL,
    PRIMARY KEY (section_id, cefr_level),
    FOREIGN KEY (section_id) REFERENCES sections(section_id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create indexes
CREATE INDEX idx_articles_date ON articles(date);
CREATE INDEX idx_articles_source ON articles(source);
