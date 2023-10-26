import json
from xuearticle import XueArticle

def download_and_process_article(topic=None, url=None, articles_dir="./articles/"):
    # download article
    article = XueArticle(topic, url)

    # process article
    article.simplify_text()
    article.generate_dict()

    # save the article
    article.save_to_json(articles_dir)

    return article

def get_news_from_url(urls):
    for url in urls:
        try:
            download_and_process_article(url=url)
        except Exception as e:
            print(f"Error downloading article from {url}: {e}")
            continue
    return

def daily_news_run():

    for topic in ["英超", "足球" ]:
        try:
            article = download_and_process_article(topic=topic)
        except Exception as e:
            print(f"Error downloading article with topic {topic}: {e}")
            continue
        if article:
            # read in article list
            try:
                with open("articles/articles.json", 'r') as file:
                    article_list = json.load(file)
            except FileNotFoundError:
                article_list = []  # Create an empty list if the file doesn't exist
            except json.decoder.JSONDecodeError:
                article_list = []  # Handle the case of an empty or invalid JSON file
            # add new articleId 
            article_list.append(article.article_id)
            # save list
            with open("articles/articles.json", 'w') as file:
                json.dump(article_list, file, indent=4)
    return 



if __name__=="__main__":
    #daily_news_run()
    urls=["https://tw.news.yahoo.com/2023%E5%AE%9C%E8%98%AD%E5%9C%8B%E9%9A%9B%E7%B6%A0%E8%89%B2%E5%BD%B1%E5%B1%9511-4%E8%B5%B7-%E5%90%8C%E6%84%9F%E5%8F%97%E7%BE%8E%E9%BA%97%E6%98%9F%E7%90%83-092241724.html"]
    get_news_from_url(urls)
