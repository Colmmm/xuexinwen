# config.py
import os

class Config:
    is_production = os.getenv('BACKEND_PRODUCTION', 'false').lower() == 'true'

    if is_production:
        REACT_APP_API_URL = "http://xue-xinwen.com:5000"
        REACT_APP_URL = "http://xue-xinwen.com"
        FLASK_ENV= "production"

    else:
        REACT_APP_API_URL = "http://localhost:5000" 
        REACT_APP_URL = "http://localhost:3000"
        FLASK_ENV= "development"
