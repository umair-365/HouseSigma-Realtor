from dotenv import load_dotenv
import os

load_dotenv()
ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')
USERNAME = os.getenv('HOUSESIGMA_USER')
PASSWORD = os.getenv('HOUSESIGMA_PASSWORD')
