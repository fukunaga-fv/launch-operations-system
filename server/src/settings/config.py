import json

# JSONファイルを開いて読み込む
def open_json(file_path: str) -> dict:
    with open(file_path, "r") as file:
        data = json.load(file)
    return data

# TODO あとでリファクタリングする

FLIGHT_PLANS = open_json("src/settings/flight_plans.json")
ROCKET_SCHEMAS = open_json("src/settings/rocket_schema.json")
rocket_schema_list = ROCKET_SCHEMAS.get("rocket_schemas", [])

# パーツのステータスコードの定義
STANDBY = 0 # 待機中
ACTIVE = 1 # アクティブ
DETACHED = 2 # 分離済み


# イベントのステータスコードの定義
IMPORTANT = 2 # 重要
NORMAL = 1 # 通常
INFO = 0 # 情報