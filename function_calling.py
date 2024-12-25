from src.openai import Agent


def main():
    agent = Agent(
        "credentials/maiko-ai/openai.json",
        use_tools=True,
        model="gpt-4o-mini",
    )
    while True:
        user_input = input("\nInput: ")
        if user_input.lower() == "quit":
            break

        result = agent.process_user_input(user_input)
        print(f"Output: {result}")


if __name__ == "__main__":
    main()
