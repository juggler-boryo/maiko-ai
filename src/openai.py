import openai
import json
import time


class Agent:
    def __init__(
        self,
        credentials_path: str,
        model: str = "gpt-4o-mini",
        use_tools: bool = True,
        system_prompt: str = "",
    ):
        self.system_prompt = system_prompt
        if self.system_prompt != "":
            self.messages = [
                {"role": "system", "content": self.system_prompt},
            ]
        else:
            self.messages = []
        self.model = model
        self.use_tools = use_tools
        openai.api_key = self._load_access_key(credentials_path)

    def _load_access_key(self, credentials_path: str) -> str:
        try:
            with open(credentials_path, "r") as f:
                return json.load(f)["ACCESS_KEY"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Failed to load access key from {credentials_path}: {e}"
            )

    def process_user_input(self, user_input: str) -> str:
        from src.function_dict import get_tools, exec_tool

        if user_input != "":
            self.messages.append({"role": "user", "content": user_input})
        try:
            completion_params = {
                "model": self.model,
                "messages": self.messages,
            }

            if self.use_tools:
                completion_params["tools"] = get_tools()
                completion_params["tool_choice"] = "auto"

            print(self.messages)
            response = openai.chat.completions.create(**completion_params)
            message = response.choices[0].message

            if message.tool_calls:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": message.tool_calls,
                    }
                )

                for index, tool_call in enumerate(message.tool_calls):
                    if index != 0:
                        time.sleep(1)
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    print(function_name, function_args)
                    result = exec_tool(function_name, function_args)
                    result_str = str(result)
                    self.messages.append(
                        {
                            "role": "tool",
                            "content": result_str,
                            "tool_call_id": tool_call.id,
                        }
                    )

                return self.process_user_input("")

            self.messages.append({"role": "assistant", "content": message.content})
            return message.content

        except Exception as e:
            return f"エラーが発生しました / An error occurred: {str(e)}"
