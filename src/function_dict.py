import requests

# -------------------------------------------------------------------------------------------------
# TODO: add more tools


def check_heater_health() -> str:
    try:
        response = requests.get("http://192.168.2.127:28001/health")
        if response.status_code != 200:
            return f"Unexpected status code: {response.status_code}"
        return f"heater is healthy"
    except requests.RequestException as e:
        return f"Error making HTTP request: {e}"


def control_heater() -> str:
    try:
        response = requests.get("http://192.168.2.127:28001/")
        if response.status_code != 200:
            return f"Unexpected status code: {response.status_code}"
        return f"heater is triggered"
    except requests.RequestException as e:
        return f"Error making HTTP request: {e}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "check_heater_health",
            "description": "灯油ストーブサーバーのヘルスチェックを行います / Checks the health of the kerosene heater server",
        },
        "callable": check_heater_health,
    },
    {
        "type": "function",
        "function": {
            "name": "control_heater",
            "description": "灯油ストーブの電源を操作します / Controls the kerosene heater power",
        },
        "callable": control_heater,
    },
]

# -------------------------------------------------------------------------------------------------


def get_tools():
    return [{"type": tool["type"], "function": tool["function"]} for tool in tools]


def exec_tool(function_name, function_args):
    tool = next(
        (tool for tool in tools if tool["function"]["name"] == function_name), None
    )
    print(f"calling {function_name} with {function_args}...")
    if tool:
        return tool["callable"](**function_args)
    else:
        raise ValueError(f"Function {function_name} not found in tools")
