import os


class Config:
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    GOOGLE_API = os.environ.get("GOOGLE_API")
    GOOGLE_CX = os.environ.get("GOOGLE_CX")
    BING_API_KEY = os.environ.get("BING_API_KEY")
