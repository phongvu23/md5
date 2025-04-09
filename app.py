from flask import Flask, request, render_template_string, redirect, url_for, session
import hashlib
import datetime
from collections import Counter

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
        return "Khả năng có bộ đôi bất kỳ "
    return "Không có đặc biệt"

app = Flask(__name__)
app.secret_key = "supersecretkey"
users = {"Phongvu": hashlib.sha256("123".encode()).hexdigest()}  # Tài khoản admin mặc định
recent_results = []  # Lưu 20 kết quả gần nhất
comments = []  # Lưu bình luận

@app.route("/")
def home():
    return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    if username in users and users[username] == hashlib.sha256(password.encode()).hexdigest():
        session["user"] = username
        return redirect(url_for("index"))
    return "Sai tên đăng nhập hoặc mật khẩu!"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("index"))
    
    hash_input = request.form.get("hash_input", "").strip()
    if not hash_input or len(hash_input) != 32:
        return "Lỗi: Vui lòng nhập đúng chuỗi MD5 hợp lệ!"
    
    result, total = split_md5(hash_input)
    display_result = "X" if total < 11 else "T"
    analysis = analyze_result(result)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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
        current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    <marquee style="font-size: 20px; color: red; font-weight: bold;">TOOL CHECK  KEY   - {{ current_time }}</marquee>
    <marquee style="font-size: 20px; color: blue; font-weight: bold;">Chúc Bạn May Mắn</marquee>
    {% if 'user' not in session %}
        <h2>Đăng nhập</h2>
        <form method="post" action="/login">
            <input type="text" name="username" required>
            <input type="password" name="password" required>
            <button type="submit">Đăng nhập</button>
        </form>
    {% else %}
        <h2>Chào mừng, {{ session['user'] }}! <a href="/logout">(Đăng xuất)</a></h2>
        <form method="post" action="/predict">
            <input type="text" name="hash_input" required>
            <button type="submit">Dự đoán</button>
        </form>
        <form method="post" action="/clear">
            <button type="submit">Xóa Kết Quả</button>
        </form>
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
