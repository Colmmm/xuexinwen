CREATE TABLE IF NOT EXISTS articles (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255),
    text TEXT,
    url VARCHAR(2083),
    simplified_title VARCHAR(255),
    simplified_text TEXT,
    keywords JSON
);

CREATE TABLE IF NOT EXISTS Images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    article_id VARCHAR(255),
    image_url VARCHAR(2083),
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
