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
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": question}],
    stream=True,
)
first_token_time = None
for chunk in stream:
    # Azure may send chunks with no choices (e.g. content-filter metadata)
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta.content
    if delta:
        if first_token_time is None:
            first_token_time = time.time()
        print(delta, end="", flush=True)
print()
end_time = time.time()
if first_token_time is not None:
    print(f"Time to first token: {first_token_time - start_time} seconds")
print(f"Time taken: {end_time - start_time} seconds")

embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input=question
)

vector = embedding.data[0].embedding
print(f"Embedding dims: {len(vector)}, first 5: {vector[:5]}")
