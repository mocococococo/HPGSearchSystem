import google.generativeai as genai
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_key = "AIzaSyAWIislvBszNaVW_eQ_nTMrZQPq-pzXsBc" # API Keyを入力

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

DEFAULT_WEATHER_INFO = {"place": "", "budget": "", "genre": ""}

def get_weather_info_from_utterance(utterance: str) -> dict:
    if not model:
        logging.error("Geminiモデルが初期化されていません。デフォルト値を返します。")
        return DEFAULT_WEATHER_INFO.copy()

    prompt = f"""
以下のユーザ発話から、天気予報に関する情報を抽出してください。
抽出する情報は、地名（都道府県または市町村名）、日付（「今日」または「明日」）、種類（「天気」または「気温」）です。
結果は、キー "place"、"date"、"type" を持つJSONオブジェクトとして返してください。
もし情報が見つからない場合は、対応する値として空文字列 "" を使用してください。

制約:
- "place" は日本の都道府県名、または市町村名のみを対象とします。都道府県名以外は空文字列にしてください。（例：「東京」、「大阪」、「北海道」）
- "date" は 「今日」または「明日」のいずれかのみを認識します。それ以外、または言及がない場合は空文字列にしてください。
- "type" は「天気」または「気温」のいずれかのみを認識します。それ以外、または言及がない場合は空文字列にしてください。

ユーザ発話: 「{utterance}」

抽出結果 (JSON形式):
"""

    logging.info(f"Geminiに送信するプロンプト:\n---\n{prompt}\n---")

    try:
        response = model.generate_content(prompt)

        if not response.parts:
             logging.warning(f"Geminiからの応答が空またはブロックされました。 Safety feedback: {response.prompt_feedback}")
             return DEFAULT_WEATHER_INFO.copy()

        response_text = response.text.strip()
        logging.info(f"Geminiからの生レスポンス: {response_text}")

        # Markdownのコードブロック形式 (```json ... ```) を除去
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip() # 再度トリム

        # JSON文字列をPython辞書に変換
        extracted_data = json.loads(response_text)

        # 期待されるキーが存在し、値が文字列であることを確認
        place = str(extracted_data.get("place", ""))
        date = str(extracted_data.get("date", ""))
        type_ = str(extracted_data.get("type", "")) # typeは組み込み関数名なのでtype_を使用

        # 念のため、許可された値以外が含まれていないかチェック (プロンプトで指示済みだが保険)
        if date not in ["今日", "明日", ""]:
            logging.warning(f"予期しない日付 '{date}' が抽出されました。空文字に設定します。")
            date = ""
        if type_ not in ["天気", "気温", ""]:
            logging.warning(f"予期しない種類 '{type_}' が抽出されました。空文字に設定します。")
            type_ = ""

        result = {"place": place, "date": date, "type": type_}
        logging.info(f"抽出・整形後の結果: {result}")
        return result

    except json.JSONDecodeError as e:
        logging.error(f"Geminiからの応答のJSON解析に失敗しました: {e}")
        logging.error(f"解析対象のテキスト: {response_text}")
        return DEFAULT_WEATHER_INFO.copy()
    except Exception as e:
        # API呼び出し中のエラーやその他の予期せぬエラー
        logging.error(f"天気情報の抽出中に予期せぬエラーが発生しました: {e}")
        # エラーによっては response オブジェクトが存在しない可能性もある
        try:
            logging.error(f"Gemini Safety Feedback (if available): {response.prompt_feedback}")
        except AttributeError:
            pass # response オブジェクトがない場合は無視
        return DEFAULT_WEATHER_INFO.copy()
    
    
def get_restaurant_info_from_utterance(utterance: str) -> dict:
    if not model:
        logging.error("Geminiモデルが初期化されていません。デフォルト値を返します。")
        return DEFAULT_WEATHER_INFO.copy()

    prompt = f"""
以下のユーザ発話から、飲食店に関する情報を抽出してください。
抽出する情報は、地名（都道府県または市町村名）、予算の最大値、飲食店のジャンル、キーワードです。
結果は、キー "place"、"budget"、"genre" を持つJSONオブジェクトとして返してください。
"place" は最大3個、 "genre" に関しては、最大2個の値を持つリストです。要素数が0の場合、[""]を返してください。
"情報が見つからない場合のみ"対応する値として空文字列 "" を使用してください。ただし、情報を1つ以上持つ場合、空文字列を使用することは許可しません。

制約:
- "place" は日本の都道府県名、市町村名のみを対象とします。都道府県名、市町村名以外は空文字列にしてください。「県」は必要ありません。（例：「東京」、「大阪」、「北海道」）
- "bufget" は整数のみを認識します。文章中の整数の最大値を対象としてください。それ以外、または言及がない場合は空文字列にしてください。
- "genre" はユーザー発話のうち、以下に示されるジャンルの名前リストに近いもの（類似した文字列でもよい）があれば、そのジャンルの
名前を返してください。それ以外、または言及がない場合は空文字列にしてください。

{
    "居酒屋"
    "ダイニングバー・バル"
    "創作料理"
    "和食"
    "洋食"
    "イタリアン・フレンチ"
    "中華"
    "焼肉・ホルモン"
    "韓国料理"
    "アジア・エスニック料理"
    "各国料理"
    "カラオケ・パーティ"
    "バー・カクテル"
    "ラーメン"
    "お好み焼き・もんじゃ"
    "カフェ・スイーツ"
    "その他"
}


ユーザ発話: 「{utterance}」

抽出結果 (JSON形式):
"""

    logging.info(f"Geminiに送信するプロンプト:\n---\n{prompt}\n---")

    try:
        response = model.generate_content(prompt)

        if not response.parts:
             logging.warning(f"Geminiからの応答が空またはブロックされました。 Safety feedback: {response.prompt_feedback}")
             return DEFAULT_WEATHER_INFO.copy()

        response_text = response.text.strip()
        logging.info(f"Geminiからの生レスポンス: {response_text}")

        # Markdownのコードブロック形式 (```json ... ```) を除去
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip() # 再度トリム

        # JSON文字列をPython辞書に変換
        extracted_data = json.loads(response_text)

        # 期待されるキーが存在し、値が文字列であることを確認
        place = extracted_data.get("place", "")
        budget = str(extracted_data.get("budget", ""))
        genre = extracted_data.get("genre", "")
        
        if len(place) > 1 and place[-1] == "":
            place = place[:-1]
        if len(genre) > 1 and genre[-1] == "":
            genre = genre[:-1]

        # 念のため、許可された値以外が含まれていないかチェック (プロンプトで指示済みだが保険)
        if budget is None or not budget.isdigit():
            logging.warning(f"予期しない予算 '{budget}' が抽出されました。空文字に設定します。")
            budget = ""

        result = {"place": place, "budget": budget, "genre": genre}
        logging.info(f"抽出・整形後の結果: {result}")
        return result

    except json.JSONDecodeError as e:
        logging.error(f"Geminiからの応答のJSON解析に失敗しました: {e}")
        logging.error(f"解析対象のテキスト: {response_text}")
        return DEFAULT_WEATHER_INFO.copy()
    except Exception as e:
        # API呼び出し中のエラーやその他の予期せぬエラー
        logging.error(f"天気情報の抽出中に予期せぬエラーが発生しました: {e}")
        # エラーによっては response オブジェクトが存在しない可能性もある
        try:
            logging.error(f"Gemini Safety Feedback (if available): {response.prompt_feedback}")
        except AttributeError:
            pass # response オブジェクトがない場合は無視
        return DEFAULT_WEATHER_INFO.copy()


# --- 実行例 ---
if __name__ == "__main__":
    test_utterances = [
        # "大阪の明日の天気",
        "明日の天気",
        # "今日の東京の気温は？",
        # "札幌の天気について教えて", # "種類" が "天気" と解釈されるか、空になるか
        # "今日の天気",
        # "明日の気温",
        # "沖縄",              # 場所のみ
        # "いつ雨降るかな",      # 具体的な情報なし
        # "京都府の今日の天気は？",
        # "明日の名古屋の天気教えて",
        # "今日の気温",
        # "北海道の明日の気温",
        # "Hello",           # 関係ない発話
    ]

    if model: # モデルが正常に初期化された場合のみ実行
        for utt in test_utterances:
            info = get_weather_info_from_utterance(utt)
            print(f"発話: 「{utt}」 -> 抽出結果: {info}")
    else:
        print("Geminiモデルが利用できないため、テストを実行できません。")
        print("環境変数 'GEMINI_API_KEY' を設定して、再度実行してください。")
