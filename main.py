import os

from dotenv import load_dotenv

from health_care_autofiller.bot import start_app

load_dotenv()

if __name__ == "__main__":
    start_app()
