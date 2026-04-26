import re
from difflib import get_close_matches
import unicodedata

# Từ điển viết tắt mở rộng (bao gồm các biến thể viết tắt học thuật + Gen Z)
ABBREVIATIONS = {
    # Viết tắt học thuật & PTIT
    "sv": "sinh viên",
    "svien": "sinh viên",
    "sinhvien": "sinh viên",
    "ptit": "Học viện Công nghệ Bưu chính Viễn thông",
    "ctsv": "công tác sinh viên",
    "gv": "giảng viên",
    "ktx": "ký túc xá",
    "cnntt": "công nghệ thông tin",
    "cntt": "công nghệ thông tin",
    "kt": "kế toán",
    "hv": "học viện",
    "qlsv": "quản lý sinh viên",
    "hd": "hướng dẫn",
    "cb": "cán bộ",
    "pban": "phòng ban",
    "qtkd": "quản trị kinh doanh",
    "attt": "an toàn thông tin",
    "dtvt": "điện tử viễn thông",
    "cnpm": "công nghệ phần mềm",
    "cnmmt": "công nghệ đa phương tiện",
    "gpa": "điểm trung bình tích lũy",
    "clb": "câu lạc bộ",
    "khcn": "khoa học công nghệ",
    "khxh": "khoa học xã hội",
    "khmt": "khoa học máy tính",
    "ktkt": "kinh tế kế toán",
    "mk": "mật khẩu",
    "tk": "tài khoản",
    "mh": "môn học",
    "dkmh": "đăng ký môn học",
    "cn": "chuyên ngành",
    "hdsv": "hỗ trợ sinh viên",
    "hocbong": "học bổng",
    "hocphi": "học phí",
    "thuvien": "thư viện",
    "baoluu": "bảo lưu",
    "chuyennganh": "chuyên ngành",
    "dangky": "đăng ký",
    "phongban": "phòng ban",
    "phongctsv": "phòng công tác sinh viên",
    "phongdaotao": "phòng đào tạo",

    "cx": "cũng",
    "k": "không",
    "kh": "không",
    "ko": "không",
    "hok": "không",
    "hk": "không",
    "dc": "được",
    "đc": "được",
    "vs": "với",
    "mik": "mình",
    "mn": "mọi người",
    "mj": "mình",
    "b": "bạn",
    "z": "vậy",
    "zay": "vậy",
    "zậy": "vậy",
    "trc": "trước",
    "s": "sao",
    "j": "gì",
    "r": "rồi",
    "nx": "nữa",
    "đag": "đang",
    "cj": "chị",
    "ae": "anh em",
    "ahihi": "haha",
    "ib": "nhắn tin",
    "rep": "trả lời",
    "ad": "quản trị viên",
    "crush": "người mình thích",
    "ms": "mới",
    "tt": "thật tình",
    "tks": "cảm ơn",
    "thank": "cảm ơn",
    "thankyou": "cảm ơn",
    "sml": "xỉu ngang",
    "vkl": "rất",
    "vl": "rất",
    "vch": "rất",
    "vcl": "rất",
    "éo": "không",
    "v": "vậy",
    "ibfb": "nhắn tin facebook",
    "chx": "chưa",
    "t": "tôi",
    "bn": "bạn",
    "tr": "trên",
    "onl": "online",
    "ol": "online",
    "rùi": "rồi",
    "h": "giờ",
    "hnay": "hôm nay",
    "mai": "ngày mai",
    "qua": "hôm qua",
    "ik": "đi",
    "oke": "đồng ý",
    "okela": "đồng ý",
    "oki": "đồng ý",
    "okie": "đồng ý"
}

# Danh sách từ vựng chuẩn
VOCABULARY = [
    "sinh viên", "giảng viên", "cán bộ", "lớp trưởng", "ban cán sự", "cố vấn học tập",
    "ký túc xá", "công tác sinh viên", "kế toán", "học viện", "phòng ban", "phòng giáo vụ",
    "phòng kế toán", "phòng CTSV", "trung tâm khảo thí", "phòng đào tạo", "phòng hành chính",
    "phòng tài chính", "trung tâm đảm bảo chất lượng", "chương trình", "đào tạo", "học bổng",
    "mẫu đơn", "email", "thẻ sinh viên", "quy định", "nội quy", "môn học", "điểm trung bình tích lũy",
    "điểm rèn luyện", "đăng ký môn học", "chuyên ngành", "tốt nghiệp", "bảo lưu kết quả", "chuyển ngành",
    "vay vốn", "học phí", "lịch học", "lịch thi", "giấy xác nhận", "giấy tờ", "bảng điểm", "bằng tốt nghiệp",
    "thủ tục", "hồ sơ", "mật khẩu", "tài khoản", "câu lạc bộ", "kỹ năng mềm", "kỹ năng học tập",
    "kỹ năng lập kế hoạch", "hoạt động ngoại khóa", "hỗ trợ sinh viên", "chế độ một cửa", "đơn xin nghỉ học",
    "đơn xin chuyển ngành", "đơn xin bảo lưu", "công nghệ thông tin", "điện tử viễn thông", "quản trị kinh doanh",
    "marketing", "an toàn thông tin", "công nghệ đa phương tiện", "internet vạn vật", "điều khiển tự động hóa",
    "khoa học máy tính", "khoa học xã hội", "khoa học công nghệ", "kinh tế kế toán", "công nghệ phần mềm",
    "PTIT", "Học viện Công nghệ Bưu chính Viễn thông", "website", "fanpage", "thủ tục hành chính", "quy chế",
    "ưu đãi sinh viên", "ưu đãi học tập", "ưu đãi ký túc xá", "ưu đãi thư viện", "thư viện",
    "giấy tờ tùy thân", "giấy báo nhập học", "giấy báo trúng tuyển"
]

def normalize_unicode(text):
    text = unicodedata.normalize('NFKC', text)
    text = text.replace("’", "'")
    return text

def remove_accents(text):
    text = unicodedata.normalize('NFD', text)
    return ''.join([c for c in text if unicodedata.category(c) != 'Mn'])

def correct_spelling(text, vocabulary=VOCABULARY):
    words = text.split()
    corrected = []
    vocab_no_acc = [remove_accents(w.lower()) for w in vocabulary]
    for word in words:
        word_no_acc = remove_accents(word.lower())
        matches = get_close_matches(word_no_acc, vocab_no_acc, n=1, cutoff=0.8)
        if matches:
            idx = vocab_no_acc.index(matches[0])
            corrected.append(vocabulary[idx])
        else:
            corrected.append(word)
    return ' '.join(corrected)

def expand_abbreviations(text, abbreviations=ABBREVIATIONS):
    words = text.split()
    expanded = []
    for word in words:
        key = remove_accents(word.lower())
        if key in abbreviations:
            expanded.append(abbreviations[key])
        else:
            expanded.append(word)
    return ' '.join(expanded)

def normalize_text(text):
    text = normalize_unicode(text)                          # Bước 1: chuẩn unicode
    text = text.lower()                                     # Bước 2: về chữ thường
    text = expand_abbreviations(text)                       # Bước 3: thay viết tắt
    text = correct_spelling(text)                           # Bước 4: sửa chính tả
    text = re.sub(r'\s+', ' ', text).strip()    # Bước 5: chuẩn hóa khoảng trắng
    return text

# Ví dụ sử dụng
if __name__ == "__main__":
    samples = [
        "em cx la sv ptit dang can xin hocbong o ktx",
        "r oi mn ib cho mik tk nha",
        "crush cx la svien ptit z",
        "hok hieu gi het, tks ad da rep"
    ]
    for sample in samples:
        print("Trước xử lý:", sample)
        print("Sau xử lý:", normalize_text(sample))
        print()
