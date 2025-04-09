from flask import Flask, request, render_template_string, redirect, url_for, session
import hashlib
import datetime
from collections import Counter

def extract_numbers_from_md5(md5_hash):
    number = int(md5_hash, 16)
    num1 = (number % 6) + 1
    number //= 10
    num2 = (number % 6) + 1
    number //= 223
    num3 = (number % 6) + 1
    return [num1, num2, num3], num1 + num2 + num3

def analyze_result(numbers):
    count = Counter(numbers)
    if 3 in count.values():
        return "Khả năng có Bão bất kỳ"
    elif 2 in count.values():
        return "Khả năng có bộ đôi bất kỳ"
    return "Không có đặc biệt"

app = Flask(__name__)
app.secret_key = "supersecretkey"
users = {}  # Tạo Users dictionary
user_ips = {}  # Lưu trữ địa chỉ IP đã sử dụng để đăng ký
recent_results = []  # Lưu 20 kết quả gần nhất
comments = []  # Lưu bình luận

@app.route("/")
def home():
    return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    if username in users and users[username]["password"] == hashlib.sha256(password.encode()).hexdigest():
        session["user"] = username
        return redirect(url_for("index"))
    return "Sai tên đăng nhập hoặc mật khẩu!"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    user_ip = request.remote_addr  # Lấy địa chỉ IP của người dùng

    if username in users:
        return "Tên đăng nhập đã tồn tại!", 400

    if user_ip in user_ips:
        return "Một địa chỉ IP chỉ có thể đăng ký một tài khoản!", 403

    users[username] = {
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "vip_level": None,  # Mức VIP khởi tạo là None
        "predictions": 0    # Số lần dự đoán khởi tạo
    }
    user_ips[user_ip] = username  # Lưu trữ địa chỉ IP và người dùng đã đăng ký
    return "Đăng ký thành công!", 201

@app.route("/set_vip", methods=["POST"])
def set_vip():
    if users = {
    "Phongvu": {
        "password": hashlib.sha256("123".encode()).hexdigest(),  # Mã hóa mật khẩu
        "vip_level": None,
        "predictions": 0
    }
}
    
    username = request.form.get("username", "").strip()
    vip_level = request.form.get("vip_level", "").strip()

    if username not in users:
        return "Người dùng không tồn tại!", 404

    if vip_level not in ['VIP 1', 'VIP 2', 'VIP 3']:
        return "Mức VIP không hợp lệ!", 400

    users[username]["vip_level"] = vip_level
    return "Mức VIP đã được cập nhật!", 200

@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("index"))

    username = session["user"]
    user_data = users[username]

    # Kiểm tra số lần dự đoán theo cấp độ VIP
    max_predictions = 15  # Mặc định cho người dùng không có VIP
    if user_data["vip_level"] == "VIP 1" or user_data["vip_level"] == "VIP 2":
        max_predictions = 50
    elif user_data["vip_level"] == "VIP 3":
        max_predictions = float('inf')  # Không giới hạn

    if user_data["predictions"] >= max_predictions:
        return "Bạn đã vượt quá số lần dự đoán tối đa!", 403

    hash_input = request.form.get("hash_input", "").strip()
    if not hash_input or len(hash_input) != 32:
        return "Lỗi: Vui lòng nhập đúng chuỗi MD5 hợp lệ!"
    
    result, total = extract_numbers_from_md5(hash_input)
    display_result = "X" if total < 11 else "T"
    analysis = analyze_result(result)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Cập nhật số lần dự đoán
    user_data["predictions"] += 1
    
    session.update({
        "result": result,
        "total": total,
        "display_result": display_result,
        "analysis": analysis
    })
    
    recent_results.insert(0, (timestamp, result, total, display_result, analysis))
    recent_results[:] = recent_results[:20]
    
    return redirect(url_for("index"))

@app.route("/clear", methods=["POST"])
def clear():
    keys_to_remove = ["result", "total", "display_result", "analysis"]
    for key in keys_to_remove:
        session.pop(key, None)
    recent_results.clear()
    return redirect(url_for("index"))

@app.route("/comment", methods=["POST"])
def comment():
    if "user" not in session:
        return redirect(url_for("index"))
    
    comment_text = request.form.get("comment_text", "").strip()
    if comment_text:
        comments.append(comment_text)
        comments[:] = comments[-10:]
    
    return redirect(url_for("index"))

@app.route("/clear_comments", methods=["POST"])
def clear_comments():
    comments.clear()
    return redirect(url_for("index"))

@app.route("/index", methods=["GET", "POST"])
def index():
    return render_template_string(
        HTML_TEMPLATE,
        result=session.get("result"),
        total=session.get("total"),
        display_result=session.get("display_result"),
        analysis=session.get("analysis"),
        recent_results=recent_results,
        comments=comments,
        current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        current_user=session.get("user")
    )

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>KEY 3</title>
    <style>
        .red { color: red; font-weight: bold; }
        .green { color: green; font-weight: bold; }
        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0; }
            100% { opacity: 1; }
        }
        .blinking {
            font-size: 24px;
            color: red;
            font-weight: bold;
            animation: blink 1s infinite;
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <marquee style="font-size: 20px; color: red; font-weight: bold;">demo 1.0   - {{ current_time }}</marquee>
    <marquee style="font-size: 20px; color: blue; font-weight: bold;">demo1.0</marquee>
    {% if 'user' not in session %}
        <h2>Đăng nhập</h2>
        <form method="post" action="/login">
            <input type="text" name="username" required placeholder="Tên đăng nhập">
            <input type="password" name="password" required placeholder="Mật khẩu">
            <button type="submit">Đăng nhập</button>
        </form>
        <h2>Đăng ký tài khoản</h2>
        <form method="post" action="/register">
            <input type="text" name="username" required placeholder="Tên đăng nhập mới">
            <input type="password" name="password" required placeholder="Mật khẩu mới">
            <button type="submit">Đăng ký</button>
        </form>
    {% else %}
        <h2>Chào mừng, {{ session['user'] }}! <a href="/logout">(thoát)</a></h2>
        <form method="post" action="/predict">
            <input type="text" name="hash_input" required placeholder="Nhập chuỗi MD5">
            <button type="submit">Dự đoán</button>
        </form>
        <form method="post" action="/clear">
            <button type="submit">Xóa Kết Quả</button>
        </form>
        {% if session['user'] == 'Phongvu' %}
            <h2>Thay đổi mức VIP của người dùng</h2>
            <form method="post" action="/set_vip">
                <input type="text" name="username" required placeholder="Tên người dùng">
                <select name="vip_level" required>
                    <option value="VIP 1">VIP 1</option>
                    <option value="VIP 2">VIP 2</option>
                    <option value="VIP 3">VIP 3</option>
                </select>
                <button type="submit">Cập nhật mức VIP</button>
            </form>
        {% endif %}
        {% if result %}
            <h3>Kết quả: {{ total }} ({{ display_result }})</h3>
            <h3>Ba số: {{ result[0] }}, {{ result[1] }}, {{ result[2] }}</h3>
            <h3 style="color: blue;">{{ analysis }}</h3>
        {% endif %}
        {% if recent_results %}
            <h3>20 Kết Quả Gần Nhất</h3>
            <ul>
                {% for res in recent_results %}
                    <li>{{ res[0] }} - Ba số: {{ res[1][0] }}, {{ res[1][1] }}, {{ res[1][2] }} - Tổng: {{ res[2] }} ({{ res[3] }}) - {{ res[4] }}</li>
                {% endfor %}
            </ul>
        {% endif %}
    {% endif %}
    <div class="blinking">v1.0</div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
