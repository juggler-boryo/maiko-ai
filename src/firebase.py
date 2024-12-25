from firebase_admin import credentials, initialize_app, db, firestore

DB = None
RTDB = None


def initialize_firebase(cred_path: str) -> None:
    global RTDB, DB
    cred = credentials.Certificate(cred_path)
    initialize_app(
        cred,
        {
            "databaseURL": "https://aigrid-23256-default-rtdb.asia-southeast1.firebasedatabase.app",
            "storageBucket": "aigrid-23256.appspot.com",
        },
    )

    RTDB = db.reference("/")
    DB = firestore.client()
    if RTDB is None:
        raise RuntimeError("Realtime database client is nil after initialization")


initialize_firebase("credentials/aigrid/sa.json")


def get_whiteboard_data() -> str:
    whiteboard_data = RTDB.child("whiteboard").child("content").get()
    return whiteboard_data


def update_whiteboard_data(content: str, old_content: str) -> None:
    # diff old_content and content, then if more than 50 % of the content is different, error
    if abs(len(content) - len(old_content)) > len(old_content) * 0.5:
        return "ホワイトボードのデータを編集できませんでした。(理由：内容が大きく変わっています)"
    else:
        RTDB.child("whiteboard").child("content").set(content)
        return "ホワイトボードのデータを編集しました。"


def _get_user_info(uid: str) -> dict:
    return DB.collection("users").document(uid).get().to_dict()


def get_current_users() -> list[str]:
    uids_dict = RTDB.child("inoutList").get()
    uids = [uid for uid, value in uids_dict.items() if value is True]
    usernames = []
    for uid in uids:
        user_info = _get_user_info(uid)
        print(user_info)
        usernames.append(user_info["username"])
    return usernames
