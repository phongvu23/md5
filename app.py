import hashlib
import random
import string

def generate_random_result(md5_hash):
    # Chuyển mã MD5 từ hexa sang số nguyên
    number = int(md5_hash, 16)

    # Tạo các số ngẫu nhiên trong khoảng từ 1 đến 6
    num1 = (number % 6) + 1
    number = (number * 3 + 7) % (10**10)
    num2 = (number % 6) + 1
    number = (number - 5) * 2 % (10**10)
    num3 = (number % 6) + 1

    # Ánh xạ cho các số
    mapping = {
        1: '3',
        2: '2',
        3: '1',
        4: '5',
        5: '6',
        6: '4'
    }

    # Ánh xạ các số thành ký tự
    mapped_num1 = mapping[num1]
    mapped_num2 = mapping[num2]
    mapped_num3 = mapping[num3]

    # Tạo chuỗi ký tự ngẫu nhiên
    random_string = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=30))

    # Tạo chuỗi kết quả
    result = f"{mapped_num1}-{mapped_num2}-{mapped_num3}|{random_string}"
    
    return result

# Mã MD5 cần xử lý
md5_hash = "8d622b3c3a7ee3c92f5289ffe22b0882"
result = generate_random_result(md5_hash)

print("Kết quả ngẫu nhiên là:", result)
