from xuearticle import XueArticle

def download_and_process_article(topic=None, url=None, articles_dir="./articles/"):
    # download article
    article = XueArticle(topic, url)

    # process article
    article.simplify_text()
    article.generate_dict()

    # save the article
    article.save_to_json(articles_dir)

    return None


if __name__=="__main__":
    test_url="https://www.hk01.com/%E5%8D%B3%E6%99%82%E9%AB%94%E8%82%B2/951476/%E8%8B%B1%E8%B6%85-%E6%9B%BC%E8%81%AF%E9%96%80%E5%B0%87%E5%A5%A7%E6%8B%BF%E6%8B%BF%E7%8D%B2%E5%9C%8B%E7%B1%B3ceo%E5%A4%A7%E8%AE%9A-%E9%9D%9Adeal-%E4%B8%8D%E6%8E%92%E9%99%A4%E6%9C%AA%E4%BE%86%E5%9B%9E%E8%B3%BC"
    download_and_process_article(url=test_url)
