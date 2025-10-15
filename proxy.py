# proxy.py
import os, time, hmac, hashlib, base64, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_URL = "https://api.searchad.naver.com"
ACCESS_LICENSE = os.environ["ACCESS_LICENSE"]
SECRET_KEY_RAW = os.environ["SECRET_KEY_RAW"]
CUSTOMER_ID = os.environ["CUSTOMER_ID"]

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
        "X-Signature": make_signature(ts, method, path)
    }

@app.route("/keyword", methods=["GET"])
def get_keyword_volume():
    kw = request.args.get("q")
    if not kw:
        return jsonify({"error": "missing_query"}), 400

    path = "/keywordstool"
    url = BASE_URL + path
    params = {"hintKeywords": kw, "showDetail": 1}

    r = requests.get(url, headers=headers_for("GET", path), params=params)
    if r.status_code != 200:
        return jsonify({"error": f"API error {r.status_code}", "body": r.text}), r.status_code

    data = r.json()
    try:
        info = data["keywordList"][0]
        return jsonify({
            "keyword": info["relKeyword"],
            "monthlyPc": info["monthlyPcQcCnt"],
            "monthlyMobile": info["monthlyMobileQcCnt"]
        })
    except Exception:
        return jsonify({"error": "parse_failed", "raw": data})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
