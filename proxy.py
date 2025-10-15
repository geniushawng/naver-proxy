# proxy.py
import os, time, hmac, hashlib, base64, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_URL = "https://api.searchad.naver.com"

# Render 대시보드에서 넣을 환경변수
ACCESS_LICENSE = os.environ["ACCESS_LICENSE"]
SECRET_KEY_RAW = os.environ["SECRET_KEY_RAW"]
CUSTOMER_ID    = os.environ["CUSTOMER_ID"]

def make_signature(ts: str, method: str, path: str) -> str:
    msg = f"{ts}.{method}.{path}".encode("utf-8")
    sign = hmac.new(SECRET_KEY_RAW.encode("utf-8"), msg, hashlib.sha256).digest()
    return base64.b64encode(sign).decode("utf-8")

def headers_for(method: str, path: str):
    ts = str(int(time.time() * 1000))
    return {
        "X-Timestamp": ts,
        "X-API-KEY": ACCESS_LICENSE,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": make_signature(ts, method, path),
    }

@app.route("/keyword", methods=["GET"])
def get_keyword_volume():
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "missing_query", "message": "q is required"}), 400
    path = "/keywordstool"
    url = BASE_URL + path
    try:
        r = requests.get(url, headers=headers_for("GET", path),
                         params={"hintKeywords": q, "showDetail": 1}, timeout=10)
    except Exception as e:
        return jsonify({"error": "request_failed", "message": str(e)}), 500

    if r.status_code != 200:
        return jsonify({"error": f"API error {r.status_code}", "body": r.text}), r.status_code

    try:
        data = r.json()
        info = data["keywordList"][0]
        return jsonify({
            "keyword": info.get("relKeyword"),
            "monthlyPc": info.get("monthlyPcQcCnt"),
            "monthlyMobile": info.get("monthlyMobileQcCnt"),
        })
    except Exception as e:
        return jsonify({"error": "parse_failed", "message": str(e), "raw": r.text}), 500

# Render는 $PORT 환경변수를 사용함
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
