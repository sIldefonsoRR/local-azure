import time

from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint="http://localhost:4000",
    api_key="fake-key",
    api_version="2024-10-21"
)

# Get the question from the user
question = input("Enter your question: ")

print("Calling fake Azure OpenAI (LiteLLM + Ollama)...")
start_time = time.time()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": question}]
)
print(response.choices[0].message.content)
end_time = time.time()
print(f"Time taken: {end_time - start_time} seconds")

embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input=question
)

vector = embedding.data[0].embedding
print(f"Embedding dims: {len(vector)}, first 5: {vector[:5]}")
