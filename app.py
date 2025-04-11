from flask import Flask, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import datetime
from collections import Counter, deque

# Hàm trích xuất 3 số từ chuỗi MD5
def extract_numbers_from_md5(md5_hash):
    """
    Trích xuất 3 số từ mã MD5. Mỗi số nằm trong khoảng từ 1 đến 6.
    """
    if not isinstance(md5_hash, str) or len(md5_hash) != 32:
        raise ValueError("Mã MD5 phải là chuỗi 32 ký tự hexa.")
    try:
        number = int(md5_hash, 16)
    except ValueError:
        raise ValueError("Mã MD5 không hợp lệ, không thể chuyển đổi sang số nguyên.")

    num1 = (number % 6) + 1
    number //= 1000
    num2 = (number % 6) + 1
    number //= 1000
    num3 = (number % 6) + 1

    return num1, num2, num3

# Hàm phân tích kết quả
def analyze_result(numbers):
    count = Counter(numbers)
    if 3 in count.values():
        return "Khả năng có Bão bất kỳ"
    elif 2 in count.values():
        return "Khả năng có bộ đôi bất kỳ"
    return "Không có đặc biệt"

# Hàm tính xác suất
def calculate_probabilities(total_x, total_t, total_predictions):
    prob_x = (total_x / total_predictions) * 100 if total_predictions > 0 else 0
    prob_t = (total_t / total_predictions) * 100 if total_predictions > 0 else 0
    return prob_x, prob_t

# Khởi tạo Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"
users = {}
user_ips = {}
recent_results = deque(maxlen=20)

# Dữ liệu để theo dõi xác suất
statistics = {
    "total_predictions": 0,
    "total_x": 0,
    "total_t": 0
}

# Khởi tạo tài khoản admin
users["Phongvu"] = {
    "password": generate_password_hash("123"),
    "vip_level": None,
    "predictions": 0
}

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the MD5 prediction app!"})

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    if username in users and check_password_hash(users[username]["password"], password):
        session["user"] = username
        return jsonify({"message": "Đăng nhập thành công!"})
    return jsonify({"error": "Sai tên đăng nhập hoặc mật khẩu!"}), 401

@app.route("/logout")
def logout():
    session.pop("user", None)
    return jsonify({"message": "Đã đăng xuất!"})

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    user_ip = request.remote_addr

    if username in users:
        return jsonify({"error": "Tên đăng nhập đã tồn tại!"}), 400

    if user_ip in user_ips:
        return jsonify({"error": "Một địa chỉ IP chỉ có thể đăng ký một tài khoản!"}), 400

    users[username] = {
        "password": generate_password_hash(password),
        "vip_level": None,
        "predictions": 0
    }
    user_ips[user_ip] = username
    return jsonify({"message": "Đăng ký thành công!"})

@app.route("/set_vip", methods=["POST"])
def set_vip():
    if "user" not in session or session["user"] != "Phongvu":
        return jsonify({"error": "Chỉ admin mới có thể thay đổi chế độ VIP!"}), 403
    
    username = request.form.get("username", "").strip()
    vip_level = request.form.get("vip_level", "").strip()

    if username not in users:
        return jsonify({"error": "Người dùng không tồn tại!"}), 404

    if vip_level not in ['VIP 1', 'VIP 2', 'VIP 3']:
        return jsonify({"error": "Mức VIP không hợp lệ!"}), 400

    users[username]["vip_level"] = vip_level
    return jsonify({"message": "Mức VIP đã được cập nhật!"})

@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return jsonify({"error": "Bạn cần đăng nhập để dự đoán!"}), 403

    username = session["user"]
    user_data = users[username]
    
    max_predictions = 10  # Default
    if user_data["vip_level"] in ["VIP 1", "VIP 2"]:
        max_predictions = 50
    elif user_data["vip_level"] == "VIP 3":
        max_predictions = float('inf')

    if user_data["predictions"] >= max_predictions:
        return jsonify({"error": "Bạn đã vượt quá số lần dự đoán tối đa!"}), 403

    hash_input = request.form.get("hash_input", "").strip()
    if not hash_input or len(hash_input) != 32 or not all(c in '0123456789abcdef' for c in hash_input.lower()):
        return jsonify({"error": "Lỗi: Vui lòng nhập đúng chuỗi MD5 hợp lệ!"}), 400

    # Trích xuất kết quả từ MD5
    try:
        result = extract_numbers_from_md5(hash_input)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    total = sum(result)
    display_result = "X" if total < 11 else "T"
    analysis = analyze_result(result)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    user_data["predictions"] += 1
    recent_results.append((timestamp, result, total, display_result, analysis))

    # Cập nhật thống kê
    statistics["total_predictions"] += 1
    if display_result == "X":
        statistics["total_x"] += 1
    else:
        statistics["total_t"] += 1
    
    # Tính xác suất
    prob_x, prob_t = calculate_probabilities(statistics["total_x"], statistics["total_t"], statistics["total_predictions"])
    
    return jsonify({
        "result": result,
        "total": total,
        "display_result": display_result,
        "analysis": analysis,
        "probabilities": {"X": prob_x, "T": prob_t}
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
