"""Step 15: check that the Gemini key works for TrustLens.

1. Lists the Gemini 'flash' models your key can use.
2. Sends a normal question.
3. Checks tool calling: Gemini should ask to use a 'search_products' tool,
   which is how the TrustLens shopping agent will work."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_OVERRIDE = os.getenv("GEMINI_MODEL")


def list_flash_models(client):
    names = []
    for model in client.models.list():
        actions = getattr(model, "supported_actions", None) or []
        name = model.name
        skip = any(word in name for word in ("image", "tts", "live", "audio", "embedding"))
        if "generateContent" in actions and "flash" in name and not skip:
            names.append(name)
    return names


def main():
    if not API_KEY:
        print("GEMINI_API_KEY is missing from .env.")
        return

    client = genai.Client(api_key=API_KEY)

    models = list_flash_models(client)
    print("Flash models your key can use:")
    for name in models:
        print(f"  - {name}")

    model = MODEL_OVERRIDE or (models[0] if models else None)
    if not model:
        print("No suitable model found.")
        return
    print(f"\nTesting with: {model}\n")

    # Test 1: a normal answer
    reply = client.models.generate_content(
        model=model,
        contents="In one short sentence, what is a payment authorisation?",
    )
    print("Test 1 - normal answer:")
    print(f"  {reply.text.strip()}\n")

    # Test 2: tool calling
    search_tool = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="search_products",
                description="Search the shop catalogue for products.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "query": types.Schema(type="STRING", description="What to search for"),
                        "max_price_eur": types.Schema(type="NUMBER", description="Highest price in euros"),
                    },
                    required=["query"],
                ),
            )
        ]
    )

    tool_reply = client.models.generate_content(
        model=model,
        contents="Find me a laptop for university under 900 euros.",
        config=types.GenerateContentConfig(
            tools=[search_tool],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    calls = tool_reply.function_calls or []
    print("Test 2 - tool calling:")
    if calls:
        for call in calls:
            print(f"  Gemini wants to use the tool '{call.name}' with: {dict(call.args)}")
        print("\nAll Gemini checks passed.")
    else:
        print("  Gemini did not ask to use the tool. Reply was:")
        print(f"  {tool_reply.text}")


if __name__ == "__main__":
    main()