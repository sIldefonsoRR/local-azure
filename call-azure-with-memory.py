from collections import deque

from openai import AzureOpenAI

MAX_TURNS = 5

client = AzureOpenAI(
    azure_endpoint="http://localhost:4000",
    api_key="fake-key",
    api_version="2024-10-21"
)

# Each entry is a (user, assistant) pair; oldest turns drop off automatically.
# In-memory only, so history is lost when the script exits.
history = deque(maxlen=MAX_TURNS)


def build_prompt(question):
    lines = []
    for user_msg, assistant_msg in history:
        lines.append(f"User: {user_msg}")
        lines.append(f"Assistant: {assistant_msg}")
    lines.append(f"User: {question}")
    lines.append("Assistant:")
    return "\n".join(lines)


def generate_content_stream(prompt):
    """Yield reply text chunks as the model generates them."""
    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        # Azure may send chunks with no choices (e.g. content-filter metadata)
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def main():
    print(f"Chat with fake Azure OpenAI (remembers last {MAX_TURNS} turns). "
          "Type 'exit' or 'quit' to stop.")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            break

        print("Assistant: ", end="", flush=True)
        parts = []
        try:
            for text in generate_content_stream(build_prompt(question)):
                parts.append(text)
                print(text, end="", flush=True)
        except KeyboardInterrupt:
            print("\n[interrupted]")
            continue
        print()

        history.append((question, "".join(parts).strip()))

    print("Bye.")


if __name__ == "__main__":
    main()
