from flask import Flask, request, render_template_string, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import datetime
from collections import Counter, deque

# Hàm trích xuất 3 số từ chuỗi MD5
def extract_numbers_from_md5(md5_hash):
    """
    Trích xuất 3 số từ mã MD5. Mỗi số nằm trong khoảng từ 1 đến 6.
    """
    # Kiểm tra tính hợp lệ của mã MD5
    if not isinstance(md5_hash, str) or len(md5_hash) != 32:
        raise ValueError("Mã MD5 phải là chuỗi 32 ký tự hexa.")

    # Chuyển mã MD5 từ hexa sang số nguyên
    try:
        number = int(md5_hash, 16)
    except ValueError:
        raise ValueError("Mã MD5 không hợp lệ, không thể chuyển đổi sang số nguyên.")

    # Trích xuất các số trong khoảng từ 1 đến 6
    num1 = (number % 6) + 1
    number //= 1000  # Giảm độ lớn của số để tiếp tục trích xuất

    num2 = (number % 6) + 1
    number //= 1000  # Tiếp tục giảm độ lớn

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
recent_results = deque(maxlen=20)  # Lưu 20 kết quả gần nhất
comments = []

# Dữ liệu để theo dõi xác suất
total_predictions = 0
total_x = 0
total_t = 0

# Khởi tạo tài khoản admin
if "Phongvu" not in users:
    users["Phongvu"] = {
        "password": generate_password_hash("123"),
        "vip_level": None,
        "predictions": 0
    }

@app.route("/")
def home():
    return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    if username in users and check_password_hash(users[username]["password"], password):
        session["user"] = username
        return redirect(url_for("index"))
    return redirect(url_for("index", error="Sai tên đăng nhập hoặc mật khẩu!"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    user_ip = request.remote_addr

    if username in users:
        return redirect(url_for("index", error="Tên đăng nhập đã tồn tại!"))

    if user_ip in user_ips:
        return redirect(url_for("index", error="Một địa chỉ IP chỉ có thể đăng ký một tài khoản!"))

    users[username] = {
        "password": generate_password_hash(password),
        "vip_level": None,
        "predictions": 0
    }
    user_ips[user_ip] = username
    return redirect(url_for("index", success="Đăng ký thành công!"))

@app.route("/set_vip", methods=["POST"])
def set_vip():
    if "user" not in session or session["user"] != "Phongvu":
        return redirect(url_for("index", error="Chỉ admin mới có thể thay đổi chế độ VIP!"))
    
    username = request.form.get("username", "").strip()
    vip_level = request.form.get("vip_level", "").strip()

    if username not in users:
        return redirect(url_for("index", error="Người dùng không tồn tại!"))

    if vip_level not in ['VIP 1', 'VIP 2', 'VIP 3']:
        return redirect(url_for("index", error="Mức VIP không hợp lệ!"))

    users[username]["vip_level"] = vip_level
    return redirect(url_for("index", success="Mức VIP đã được cập nhật!"))

@app.route("/predict", methods=["POST"])
def predict():
    global total_predictions, total_x, total_t  # Đánh dấu để sử dụng biến toàn cục
    if "user" not in session:
        return redirect(url_for("index"))

    username = session["user"]
    user_data = users[username]
    
    max_predictions = 10  # Default
    if user_data["vip_level"] in ["VIP 1", "VIP 2"]:
        max_predictions = 50
    elif user_data["vip_level"] == "VIP 3":
        max_predictions = float('inf')

    if user_data["predictions"] >= max_predictions:
        return redirect(url_for("index", error="Bạn đã vượt quá số lần dự đoán tối đa! Liên hệ admin để kích hoạt Vip"))

    hash_input = request.form.get("hash_input", "").strip()
    if not hash_input or len(hash_input) != 32 or not all(c in '0123456789abcdef' for c in hash_input.lower()):
        return redirect(url_for("index", error="Lỗi: Vui lòng nhập đúng chuỗi MD5 hợp lệ!"))

    # Trích xuất kết quả từ MD5
    result = extract_numbers_from_md5(hash_input)
    total = sum(result)
    display_result = "X" if total < 11 else "T"
    analysis = analyze_result(result)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    user_data["predictions"] += 1
    session.update({
        "result": result,
        "total": total,
        "display_result": display_result,
        "analysis": analysis,
    })

    recent_results.append((timestamp, result, total, display_result, analysis))

    # Cập nhật tổng số lần dự đoán và số lần xuất hiện của T và X.
    total_predictions += 1
    if display_result == "X":
        total_x += 1
    else:
        total_t += 1
    
    # Tính xác suất
    prob_x, prob_t = calculate_probabilities(total_x, total_t, total_predictions)
    
    session['prob_x'] = prob_x
    session['prob_t'] = prob_t
    
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
