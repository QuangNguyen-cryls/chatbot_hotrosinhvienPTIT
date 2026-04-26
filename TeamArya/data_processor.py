import os
import re
import json
import random
from pathlib import Path
from typing import List, Tuple

from sentence_transformers import InputExample


BASE_DIR = Path(__file__).resolve().parent


def _strip_line_prefixes(raw_text: str) -> str:
    """
    Remove the leading "L<digits>:" markers from each line of the handbook file.
    """
    lines = raw_text.splitlines()
    cleaned_lines: List[str] = []
    for line in lines:
        cleaned_lines.append(re.sub(r"^L\d+:", "", line).strip())
    return "\n".join(cleaned_lines)


def remove_special_characters(text: str) -> str:
    """
    Loại bỏ ký tự đặc biệt không cần thiết nhưng giữ lại tiếng Việt có dấu,
    chữ số và các dấu câu cơ bản.
    """
    # Giữ chữ cái (kể cả có dấu), số, khoảng trắng và một số dấu câu phổ biến
    text = re.sub(r"[^\w\sÀ-ỹ.,;:?!()/%&\-]", " ", text, flags=re.UNICODE)
    return text


def normalize_whitespace(text: str) -> str:
    """Chuẩn hoá khoảng trắng."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    """
    Tokenization tối giản bằng khoảng trắng để tránh phụ thuộc thư viện ngoài.
    Trả về danh sách token.
    """
    return [tok for tok in text.split(" ") if tok]


def read_handbook_text(handbook_path: str) -> str:
    with open(handbook_path, "r", encoding="utf-8") as f:
        raw = f.read()
    raw = _strip_line_prefixes(raw)
    return raw


def split_sentences(clean_text: str) -> List[str]:
    """
    Tách câu đơn giản dựa vào dấu câu. Kết hợp với xuống dòng để giữ cấu trúc đoạn.
    """
    # Thay xuống dòng kép thành dấu chấm để cắt đoạn
    text = re.sub(r"\n{2,}", ". ", clean_text)
    # Thay xuống dòng đơn bằng khoảng trắng
    text = re.sub(r"\n", " ", text)
    # Tách theo . ! ? ; :
    parts = re.split(r"(?<=[\.!?;:])\s+", text)
    sentences: List[str] = []
    for s in parts:
        s = normalize_whitespace(s)
        if len(s) > 0:
            sentences.append(s)
    return sentences


def build_positive_pairs(sentences: List[str], window: int = 1,
                          min_chars: int = 25, max_chars: int = 350) -> List[Tuple[str, str]]:
    """
    Tạo cặp câu dương tính (anchor, positive) bằng cách ghép các câu lân cận.
    """
    pairs: List[Tuple[str, str]] = []
    filtered = [s for s in sentences if min_chars <= len(s) <= max_chars]
    for i in range(len(filtered) - window):
        anchor = filtered[i]
        positive = filtered[i + window]
        if anchor != positive:
            pairs.append((anchor, positive))
    return pairs


def save_pairs_to_jsonl(pairs: List[Tuple[str, str]], jsonl_path: str) -> str:
    os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for a, p in pairs:
            f.write(json.dumps({"texts": [a, p], "label": 1.0}, ensure_ascii=False) + "\n")
    return jsonl_path


def load_input_examples(jsonl_path: str, limit: int | None = None) -> List[InputExample]:
    examples: List[InputExample] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if limit is not None and idx >= limit:
                break
            item = json.loads(line)
            a, p = item["texts"]
            examples.append(InputExample(texts=[a, p]))
    return examples


def build_dataset_from_handbook(handbook_path: str,
                                output_jsonl: str | None = None,
                                seed: int = 42) -> str:
    """
    Thực hiện pipeline theo sơ đồ: nhập input -> loại ký tự đặc biệt -> chuẩn hoá
    -> tokenization (đơn giản) -> sinh cặp câu -> lưu JSONL.
    Trả về đường dẫn file JSONL.
    """
    random.seed(seed)

    raw_text = read_handbook_text(handbook_path)
    cleaned = normalize_whitespace(remove_special_characters(raw_text))

    # Tokenization step is executed but we don't use tokens further; it's part of the pipeline.
    _ = tokenize(cleaned)

    sentences = split_sentences(cleaned)
    pairs = build_positive_pairs(sentences)

    if output_jsonl is None:
        output_jsonl = str(BASE_DIR / "datasets" / "ptit_pairs.jsonl")

    save_pairs_to_jsonl(pairs, output_jsonl)
    return output_jsonl


def get_corpus_sentences(handbook_path: str,
                         min_chars: int = 25,
                         max_chars: int = 450) -> List[str]:
    """Trả về danh sách câu/đoạn đã làm sạch.

    Cải tiến: Gộp các tiêu đề/ngắn (kết thúc bằng ':' hoặc độ dài < 20)
    với 1-2 câu tiếp theo để tạo chunk giàu ngữ nghĩa hơn.
    """
    raw = read_handbook_text(handbook_path)
    cleaned = normalize_whitespace(remove_special_characters(raw))
    sentences = split_sentences(cleaned)

    merged: List[str] = []
    i = 0
    while i < len(sentences):
        s = sentences[i]
        is_heading = s.endswith(":") or len(s) < 20
        if is_heading:
            parts = [s]
            # Gộp tối đa 2 câu tiếp theo nếu còn ngắn
            j = 1
            while j <= 2 and (i + j) < len(sentences):
                parts.append(sentences[i + j])
                j += 1
            chunk = normalize_whitespace(" ".join(parts))
            merged.append(chunk)
            i += j
        else:
            merged.append(s)
            i += 1

    return [m for m in merged if min_chars <= len(m) <= max_chars]


if __name__ == "__main__":
    hb_path = str(BASE_DIR / "handbook_summary.txt")
    out_path = str(BASE_DIR / "datasets" / "ptit_pairs.jsonl")
    dataset_path = build_dataset_from_handbook(hb_path, out_path)
    examples = load_input_examples(dataset_path, limit=5)
    print(f"Created dataset at: {dataset_path}")
    print(f"Preview pairs: {len(examples)} examples, first 1:")
    if examples:
        print(json.dumps({"texts": examples[0].texts}, ensure_ascii=False))


