import re

def is_valid_vietnamese(text):
    # Danh sách các ký tự hợp lệ trong tiếng Việt
    vietnamese_chars = "aáàảãạăắằẳẵặâấầẩẫậbcdđeéèẻẽẹêếềểễệfghiíìỉĩịjklmnoóòỏõọôốồổỗộơớờởỡợpqrs"
    vietnamese_chars += "tuúùủũụưứừửữựvwx"
    vietnamese_chars += "yýỳỷỹỵzAÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬBCDĐEÉÈẺẼẸÊẾỀỂỄỆFGHIÍÌỈĨỊJKLMNOÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢPQRS"
    vietnamese_chars += "TUÚÙỦŨỤƯỨỪỬỮỰVWX"
    vietnamese_chars += "YÝỲỶỸỴZ0123456789.,- "

    # Kiểm tra từng ký tự có thuộc danh sách tiếng Việt hay không
    return all(c in vietnamese_chars for c in text)

# Test cases
print(is_valid_vietnamese("Tr蘯ァn Anh Vナゥ"))  # False
print(is_valid_vietnamese("Trần Anh Vũ"))       # True
print(is_valid_vietnamese("Nguyễn Văn A"))      # True
print(is_valid_vietnamese("Lê Quang 123"))      # True
print(is_valid_vietnamese("Test $%^&*"))        # False
