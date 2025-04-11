<!DOCTYPE html>
<html lang="vi">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Random Result Generator</title>
</head>

<body>
    <h1>Generator Kết Quả Ngẫu Nhiên</h1>
    <input type="text" id="md5Hash" placeholder="Nhập mã MD5">
    <button onclick="generateResult()">Tạo Kết Quả</button>
    <p id="result"></p>

    <script>
        function generateRandomResult(md5Hash) {
            // Kiểm tra tính hợp lệ của mã MD5
            if (typeof md5Hash !== 'string' || md5Hash.length !== 32 || !/^[0-9a-f]+$/.test(md5Hash.toLowerCase())) {
                throw new Error("Mã MD5 không hợp lệ. Vui lòng nhập chuỗi MD5 gồm 32 ký tự hexa.");
            }

            // Chuyển mã MD5 từ hexa sang số nguyên
            let number = BigInt(`0x${md5Hash}`);

            // Tạo các số ngẫu nhiên trong khoảng từ 1 đến 6
            let num1 = (number % 6n) + 1n;
            number = (number * 3n + 7n) % 10000000000n;
            let num2 = (number % 6n) + 1n;
            number = (number - 5n) * 2n % 10000000000n;
            let num3 = (number % 6n) + 1n;

            // Ánh xạ cho các số
            const mapping = {
                1n: '3',
                2n: '2',
                3n: '1',
                4n: '5',
                5n: '6',
                6n: '4'
            };

            // Ánh xạ các số thành ký tự
            const mappedNum1 = mapping[num1];
            const mappedNum2 = mapping[num2];
            const mappedNum3 = mapping[num3];

            // Tạo chuỗi ký tự ngẫu nhiên
            const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()';
            let randomString = '';
            for (let i = 0; i < 30; i++) {
                randomString += characters.charAt(Math.floor(Math.random() * characters.length));
            }

            // Tạo chuỗi kết quả
            return `${mappedNum1}-${mappedNum2}-${mappedNum3}|${randomString}`;
        }

        function generateResult() {
            const md5Hash = document.getElementById("md5Hash").value;
            try {
                const result = generateRandomResult(md5Hash);
                document.getElementById("result").innerText = "Kết quả ngẫu nhiên là: " + result;
            } catch (e) {
                document.getElementById("result").innerText = "Lỗi: " + e.message;
            }
        }
    </script>
</body>

</html>
