from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint="http://localhost:4000",
    api_key="fake-key",
    api_version="2024-10-21"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello from LiteLLM + Ollama!"}]
)

print(response.choices[0].message.content)

embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input="Hello from LiteLLM + Ollama!"
)

vector = embedding.data[0].embedding
print(f"Embedding dims: {len(vector)}, first 5: {vector[:5]}")
