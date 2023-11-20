# config.py
import os

class Config:
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    if FLASK_ENV=='production':
        REACT_APP_API_URL = "http://xue-xinwen.com:5000"
        REACT_APP_URL = "http://xue-xinwen.com"

    if FLASK_ENV=='development':
        REACT_APP_API_URL = "http://xue-xinwen.com:5000"
        REACT_APP_URL = "http://xue-xinwen.com"