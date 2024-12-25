import json
import openai
from src.function_dict import get_tools, exec_tool


def _load_access_key(credentials_path: str) -> str:
    try:
        with open(credentials_path, "r") as f:
            return json.load(f)["ACCESS_KEY"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to load access key from {credentials_path}: {e}")


messages = []

openai.api_key = _load_access_key("credentials/maiko-ai/openai.json")


def process_user_input(user_input: str) -> str:
    if user_input != "":
        messages.append({"role": "user", "content": user_input})
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=get_tools(),
            tool_choice="auto",
        )

        message = response.choices[0].message

        if message.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                }
            )

            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                result = exec_tool(function_name, function_args)
                result_str = str(result)
                messages.append(
                    {
                        "role": "tool",
                        "content": result_str,
                        "tool_call_id": tool_call.id,
                    }
                )

            return process_user_input("")

        messages.append({"role": "assistant", "content": message.content})
        return message.content

    except Exception as e:
        return f"エラーが発生しました / An error occurred: {str(e)}"


def main():
    while True:
        user_input = input("\nInput: ")
        if user_input.lower() == "quit":
            break

        result = process_user_input(user_input)
        print(f"Output: {result}")


if __name__ == "__main__":
    main()
