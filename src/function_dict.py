import requests
from src.firebase import get_whiteboard_data

# -------------------------------------------------------------------------------------------------
# TODO: add more tools


def check_heater_health_tool() -> str:
    try:
        response = requests.get("http://192.168.2.127:28001/health")
        if response.status_code != 200:
            return f"Unexpected status code: {response.status_code}"
        return f"heater is healthy"
    except requests.RequestException as e:
        return f"Error making HTTP request: {e}"


def control_heater_tool() -> str:
    try:
        response = requests.get("http://192.168.2.127:28001/")
        if response.status_code != 200:
            return f"Unexpected status code: {response.status_code}"
        return f"heater is triggered"
    except requests.RequestException as e:
        return f"Error making HTTP request: {e}"


def get_whiteboard_data_tool() -> str:
    return get_whiteboard_data()


tools = [
    {
        "type": "function",
        "function": {
            "name": "check_heater_health",
            "description": "灯油ストーブサーバーのヘルスチェックを行います。",
        },
        "callable": check_heater_health_tool,
    },
    {
        "type": "function",
        "function": {
            "name": "control_heater",
            "description": "灯油ストーブの電源を操作します。",
        },
        "callable": control_heater_tool,
    },
    {
        "type": "function",
        "function": {
            "name": "get_whiteboard_data",
            "description": "ホワイトボードのデータを取得します。ホワイトボードには生活のTODOや、食材、その他のメモを記録しています。",
        },
        "callable": get_whiteboard_data_tool,
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
