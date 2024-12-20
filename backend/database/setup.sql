-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS word_levels;
DROP TABLE IF EXISTS entities;
DROP TABLE IF EXISTS graded_content;
DROP TABLE IF EXISTS articles;

-- Create articles table with full content storage
CREATE TABLE articles (
    article_id VARCHAR(16) PRIMARY KEY,
    url VARCHAR(512) UNIQUE NOT NULL,
    date TIMESTAMP NOT NULL,
    source VARCHAR(32) NOT NULL,
    authors JSON NOT NULL,  -- Store authors as JSON array
    mandarin_title TEXT NOT NULL,
    english_title TEXT NOT NULL,
    mandarin_content TEXT NOT NULL,
    english_content TEXT NOT NULL,
    section_indices JSON NOT NULL,  -- Store as array of [start, end] pairs
    image_url VARCHAR(512),
    metadata JSON,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create graded_content table for simplified versions
CREATE TABLE graded_content (
    article_id VARCHAR(16),
    cefr_level ENUM('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (article_id, cefr_level),
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create entities table for named entity recognition results
CREATE TABLE entities (
    article_id VARCHAR(16),
    entity_text VARCHAR(255) NOT NULL,
    entity_type ENUM('person', 'place', 'organization', 'other') NOT NULL,
    english_definition TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (article_id, entity_text),
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create word_levels table for TOCFL/CEFR level assignments
CREATE TABLE word_levels (
    article_id VARCHAR(16),
    word VARCHAR(255) NOT NULL,
    cefr_level ENUM('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'unknown') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (article_id, word),
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create indexes
CREATE INDEX idx_articles_date ON articles(date);
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_processed ON articles(processed);
CREATE INDEX idx_graded_content_level ON graded_content(cefr_level);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_word_levels_level ON word_levels(cefr_level);

-- Create views for analysis
CREATE VIEW article_statistics AS
SELECT 
    a.article_id,
    a.source,
    a.date,
    COUNT(DISTINCT e.entity_text) as entity_count,
    COUNT(DISTINCT w.word) as unique_words,
    COUNT(DISTINCT g.cefr_level) as graded_versions
FROM articles a
LEFT JOIN entities e ON a.article_id = e.article_id
LEFT JOIN word_levels w ON a.article_id = w.article_id
LEFT JOIN graded_content g ON a.article_id = g.article_id
GROUP BY a.article_id, a.source, a.date;
