from flask import Flask, request, render_template_string, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import datetime
from collections import Counter, deque

def split_md5(hash_str):
    part_length = len(hash_str) // 3
    parts = [hash_str[i * part_length: (i + 1) * part_length] for i in range(3)]
    numbers = [(int(part, 16) % 6) + 1 for part in parts]
    return numbers, sum(numbers)

def analyze_result(numbers):
    count = Counter(numbers)
    if 3 in count.values():
        return "Khả năng có Bão bất kỳ"
    elif 2 in count.values():
        return "Khả năng có bộ đôi bất kỳ"
    return "Không có đặc biệt"

app = Flask(__name__)
app.secret_key = "supersecretkey"
users = {}
user_ips = {}
recent_results = deque(maxlen=20)  # Sử dụng deque để giữ 20 kết quả gần nhất
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
    
    max_predictions = 15  # Default
    if user_data["vip_level"] in ["VIP 1", "VIP 2"]:
        max_predictions = 50
    elif user_data["vip_level"] == "VIP 3":
        max_predictions = float('inf')

    if user_data["predictions"] >= max_predictions:
        return redirect(url_for("index", error="Bạn đã vượt quá số lần dự đoán tối đa!"))

    hash_input = request.form.get("hash_input", "").strip()
    if not hash_input or len(hash_input) != 32 or not all(c in '0123456789abcdef' for c in hash_input.lower()):
        return redirect(url_for("index", error="Lỗi: Vui lòng nhập đúng chuỗi MD5 hợp lệ!"))

    result, total = split_md5(hash_input)
    display_result = "X" if total < 11 else "T"
    analysis = analyze_result(result)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    user_data["predictions"] += 1
    session.update({
        "result": result,
        "total": total,
        "display_result": display_result,
        "analysis": analysis
    })

    recent_results.append((timestamp, result, total, display_result, analysis))

    # Cập nhật tổng số lần dự đoán và số lần xuất hiện của T và X.
    total_predictions += 1
    if display_result == "X":
        total_x += 1
    else:
        total_t += 1
    
    # Tính xác suất
    prob_x = (total_x / total_predictions) * 100 if total_predictions > 0 else 0
    prob_t = (total_t / total_predictions) * 100 if total_predictions > 0 else 0

    session['prob_x'] = prob_x
    session['prob_t'] = prob_t
    
    return redirect(url_for("index"))

@app.route("/clear", methods=["POST"])
def clear():
    for key in ["result", "total", "display_result", "analysis", "prob_x", "prob_t"]:
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
        comments[:] = comments[-10:]  # Giới hạn bình luận gần nhất xuống 10

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
        current_user=session.get("user"),
        users=users,  # Gửi dictionary users để truy cập thông tin về mức VIP
        error=request.args.get("error"),
        success=request.args.get("success"),
        prob_x=session.get('prob_x', 0),  # Xác suất của X
        prob_t=session.get('prob_t', 0)   # Xác suất của T
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
    {% if error %}
        <h3 class="red">{{ error }}</h3>
    {% endif %}
    {% if success %}
        <h3 class="green">{{ success }}</h3>
    {% endif %}
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
        <h2>Chào mừng, {{ current_user }}! (Mức VIP: {{ users[current_user].get('vip_level', 'Không có') }}) <a href="/logout">(thoát)</a></h2>
        <form method="post" action="/predict">
            <input type="text" name="hash_input" required placeholder="Nhập chuỗi MD5">
            <button type="submit">Dự đoán</button>
        </form>
        <form method="post" action="/clear">
            <button type="submit">Xóa Kết Quả</button>
        </form>
        {% if current_user == 'Phongvu' %}
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
            <h3>Xác suất X: {{ prob_x|round(2) }}%</h3>
            <h3>Xác suất T: {{ prob_t|round(2) }}%</h3>
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
