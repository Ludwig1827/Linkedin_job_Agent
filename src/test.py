import os
from dotenv import load_dotenv
load_dotenv(override=True)
print(os.getenv("OPENAI_API_KEY"))