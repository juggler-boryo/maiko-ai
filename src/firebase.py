from firebase_admin import credentials, initialize_app, db

RTDB = None


def initialize_firebase(cred_path: str) -> None:
    global RTDB
    cred = credentials.Certificate(cred_path)
    initialize_app(
        cred,
        {
            "databaseURL": "https://aigrid-23256-default-rtdb.asia-southeast1.firebasedatabase.app",
            "storageBucket": "aigrid-23256.appspot.com",
        },
    )

    RTDB = db.reference("/")

    if RTDB is None:
        raise RuntimeError("Realtime database client is nil after initialization")


initialize_firebase("credentials/aigrid/sa.json")


def get_whiteboard_data() -> str:
    whiteboard_data = RTDB.child("whiteboard").child("content").get()
    return whiteboard_data


def update_whiteboard_data(content: str, old_content: str) -> str:
    # diff old_content and content, then if more than 50 % of the content is different, error
    if abs(len(content) - len(old_content)) > len(old_content) * 0.5:
        return "ホワイトボードのデータを編集できませんでした。(理由：内容が大きく変わっています)"
    else:
        RTDB.child("whiteboard").child("content").set(content)
        return "ホワイトボードのデータを編集しました。"
