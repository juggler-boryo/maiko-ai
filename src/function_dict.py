from src.tools import (
    check_heater_health_tool,
    control_heater_tool,
    get_whiteboard_data_tool,
    edit_whiteboard_data_tool,
    get_current_users_tool,
)

tools = [
    {
        "type": "function",
        "name": "check_heater_health",
        "description": "灯油ストーブサーバーのヘルスチェックを行います。",
        "callable": check_heater_health_tool,
    },
    {
        "type": "function", 
        "name": "control_heater",
        "description": "灯油ストーブの電源を操作します。",
        "callable": control_heater_tool,
    },
    {
        "type": "function",
        "name": "get_whiteboard_data", 
        "description": "ホワイトボードのデータを取得します。ホワイトボードには生活のTODOや、食材、その他のメモを記録しています。",
        "callable": get_whiteboard_data_tool,
    },
    {
        "type": "function",
        "name": "edit_whiteboard_data",
        "description": "ホワイトボードのデータを部分的に編集します。",
        "parameters": {
            "type": "object",
            "required": ["content"],
            "properties": {
                "content": {
                    "type": "string",
                    "description": "ホワイトボードのデータを編集するためのクエリ。短く具体的に。例えば、'納豆を買う'とか'うどんを一つ食べた'とか'HOGEのTODOを追加'とか。",
                },
            },
        },
        "callable": edit_whiteboard_data_tool,
    },
    {
        "type": "function",
        "name": "get_current_users",
        "description": "現在のユーザーを取得します。",
        "callable": get_current_users_tool,
    },
]


def get_tools():
    # return tool but without callable and include parameters if present
    return [{
        "type": tool["type"],
        "name": tool["name"], 
        "description": tool["description"],
        "parameters": tool.get("parameters")
    } for tool in tools]

def exec_tool(function_name, function_args):
    tool = next(
        (tool for tool in tools if tool["name"] == function_name), None
    )
    print(f"calling {function_name} with {function_args}...")
    if tool:
        return tool["callable"](**function_args)
    else:
        raise ValueError(f"Function {function_name} not found in tools")
