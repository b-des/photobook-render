import os


APP_ENV = os.environ.get('APP_ENV', 'development')
API_PREFIX = "/api"
HEALTH_PREFIX = "/health"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = "logs" if APP_ENV == "development" else "/tmp/photobook/logs"
LOG_FILE = f"{LOG_DIR}/log.txt"
DOMAINS_DICT_FILE = os.environ.get('DOMAINS_DICT_PATH', "domains.json")
