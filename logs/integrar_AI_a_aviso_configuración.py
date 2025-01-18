from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(model="o1-mini-2024-09-12", messages=[])
