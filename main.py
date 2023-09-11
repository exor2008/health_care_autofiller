import os

from dotenv import load_dotenv

from health_care_autofiller.render import Parser

load_dotenv()

if __name__ == "__main__":
    with Parser(os.getenv("TEMPLATE"), "Vasya Pupkin") as p:
        p.fill()
