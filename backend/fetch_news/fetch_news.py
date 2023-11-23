import json
from xuearticle import XueArticle
import pytz
from datetime import datetime, time
from apscheduler.schedulers.blocking import BlockingScheduler


def download_and_process_article(topic=None, url=None, articles_dir="../articles/"):
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

def daily_news_run(articles_dir="../articles/"):

    for topic in ["英超", "足球" ]:
        try:
            article = download_and_process_article(topic=topic)
        except Exception as e:
            print(f"Error downloading article with topic {topic}: {e}")
            continue
        if article:
            # read in article list
            try:
                with open(f"{articles_dir}/articles.json", 'r') as file:
                    article_list = json.load(file)
            except FileNotFoundError:
                article_list = []  # Create an empty list if the file doesn't exist
            except json.decoder.JSONDecodeError:
                article_list = []  # Handle the case of an empty or invalid JSON file
            # add new articleId 
            article_list.append(article.article_id)
            # save list
            with open(f"{articles_dir}/articles.json", 'w') as file:
                json.dump(article_list, file, indent=4)
    return 


# Create a scheduler
scheduler = BlockingScheduler()

# Set the timezone
tw = pytz.timezone('Asia/Taipei')

# Define the task to run daily at 5 am in the specified timezone
@scheduler.scheduled_job('cron', hour=5, minute=0, second=0, timezone=tw)
def scheduled_daily_news_run():
    current_time = datetime.now(tw)
    print(f"Running daily_news_run at {current_time}")
    daily_news_run()

# Start the scheduler
scheduler.start()
