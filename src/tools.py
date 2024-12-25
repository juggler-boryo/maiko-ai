import requests
from src.firebase import get_whiteboard_data, update_whiteboard_data
from src.openai import Agent


def check_heater_health_tool() -> str:
    try:
        response = requests.get("http://192.168.2.127:28001/health", timeout=5)
        if response.status_code != 200:
            return f"Unexpected status code: {response.status_code}"
        return f"heater is healthy"
    except requests.RequestException as e:
        return f"Error making HTTP request: {e}"
    except Exception as e:
        return f"エラーが発生しました / An error occurred: {str(e)}"


def control_heater_tool() -> str:
    try:
        response = requests.get("http://192.168.2.127:28001/", timeout=5)
        if response.status_code != 200:
            return f"Unexpected status code: {response.status_code}"
        return f"heater is triggered"
    except requests.RequestException as e:
        return f"Error making HTTP request: {e}"
    except Exception as e:
        return f"エラーが発生しました / An error occurred: {str(e)}"


def get_whiteboard_data_tool() -> str:
    return get_whiteboard_data()


def edit_whiteboard_data_tool(content: str) -> str:
    old_content = get_whiteboard_data()
    agent = Agent(
        "credentials/maiko-ai/openai.json",
        use_tools=False,
        model="gpt-4o",
        system_prompt=f"あなたはシェアハウスのTODO管理アシスタントです。ユーザーから与えられたホワイトボードの内容を'{content}'に従って編集し、編集後のホワイトボードの内容のみを返してください。",
    )
    processed_content = agent.process_user_input(old_content)
    return update_whiteboard_data(processed_content, old_content)
