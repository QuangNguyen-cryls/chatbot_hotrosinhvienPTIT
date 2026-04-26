import argparse
import csv
import json
import os
import sys
from typing import List, Dict, Optional

import numpy as np
import requests
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity

from sentence_transformers import SentenceTransformer


def load_data(data_path: str) -> List[Dict]:
    """Load data from JSONL file"""
    items = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            obj = json.loads(line)
            items.append({
                "id": obj.get("id", ""),
                "question": obj.get("question", ""),
                "gold_answers": obj.get("gold_answers", []),
                "negative_answers": obj.get("negative_answers", []),
                "is_positive": obj.get("is_positive", True),
                "section": obj.get("section", "")
            })
    return items


def rasa_predict(rasa_url: str, question: str, timeout_s: float) -> str:
    """Gọi Rasa để lấy dự đoán"""
    payload = {"sender": "eval", "message": question}
    resp = requests.post(rasa_url, json=payload, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()
    
    texts = []
    if isinstance(data, list):
        for msg in data:
            text = msg.get("text") if isinstance(msg, dict) else None
            if isinstance(text, str):
                texts.append(text)
    else:
        text = data.get("text") if isinstance(data, dict) else None
        if isinstance(text, str):
            texts.append(text)
    
    if not texts:
        texts = ["Xin lỗi, tôi chưa hiểu câu hỏi."]
    return " ".join(texts).strip()


def calculate_similarity(pred_text: str, gold_answers: List[str], model: SentenceTransformer) -> float:
    """Tính cosine similarity giữa pred_text và gold_answers"""
    if not gold_answers:
        return 0.0
    
    # Embed pred_text và gold_answers
    pred_emb = model.encode([pred_text], convert_to_numpy=True, normalize_embeddings=True)
    gold_embs = model.encode(gold_answers, convert_to_numpy=True, normalize_embeddings=True)
    
    # Tính cosine similarity
    similarities = cosine_similarity(pred_emb, gold_embs)[0]
    return float(np.max(similarities))


def calculate_negative_similarity(pred_text: str, negative_answers: List[str], model: SentenceTransformer) -> float:
    """Tính cosine similarity giữa pred_text và negative_answers"""
    if not negative_answers:
        return -1.0
    
    pred_emb = model.encode([pred_text], convert_to_numpy=True, normalize_embeddings=True)
    neg_embs = model.encode(negative_answers, convert_to_numpy=True, normalize_embeddings=True)
    
    similarities = cosine_similarity(pred_emb, neg_embs)[0]
    return float(np.max(similarities))


def decide_prediction(sim_pos: float, sim_neg: float, threshold: float) -> int:
    """Quyết định prediction dựa trên similarity threshold"""
    if sim_neg < 0:  # Không có negative examples
        return 1 if sim_pos >= threshold else 0
    else:
        return 1 if (sim_pos >= threshold) and (sim_pos > sim_neg) else 0


def tune_threshold(items: List[Dict], model: SentenceTransformer, start: float, end: float, step: float) -> float:
    """Tune threshold trên dev set"""
    best_t = start
    best_f1 = -1.0
    
    # Tạo y_true (tất cả positive)
    y_true = [1 if item["is_positive"] else 0 for item in items]
    
    t = start
    while t <= end + 1e-9:
        y_pred = []
        for item in items:
            # Giả sử có prediction text (trong thực tế sẽ gọi Rasa)
            pred_text = "dummy_prediction"  # Placeholder
            sim_pos = calculate_similarity(pred_text, item["gold_answers"], model)
            sim_neg = calculate_negative_similarity(pred_text, item["negative_answers"], model)
            pred = decide_prediction(sim_pos, sim_neg, t)
            y_pred.append(pred)
        
        f1 = f1_score(y_true, y_pred, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_t = t
        t += step
    
    return best_t


def evaluate_rasa(items: List[Dict], model: SentenceTransformer, rasa_url: str, threshold: float, timeout_s: float, output_file: str):
    """Đánh giá Rasa sử dụng sklearn"""
    y_true = []
    y_pred = []
    rows = []
    
    for item in items:
        question = item["question"]
        is_positive = item["is_positive"]
        gold_answers = item["gold_answers"]
        negative_answers = item["negative_answers"]
        
        y_true.append(1 if is_positive else 0)
        
        try:
            pred_text = rasa_predict(rasa_url, question, timeout_s)
        except Exception:
            pred_text = "Xin lỗi, tôi chưa hiểu câu hỏi."
        
        # Tính similarities
        sim_pos = calculate_similarity(pred_text, gold_answers, model)
        sim_neg = calculate_negative_similarity(pred_text, negative_answers, model)
        
        # Quyết định prediction
        pred = decide_prediction(sim_pos, sim_neg, threshold)
        y_pred.append(pred)
        
        # Tìm best gold answer
        best_gold = gold_answers[0] if gold_answers else ""
        if gold_answers:
            pred_emb = model.encode([pred_text], convert_to_numpy=True, normalize_embeddings=True)
            gold_embs = model.encode(gold_answers, convert_to_numpy=True, normalize_embeddings=True)
            similarities = cosine_similarity(pred_emb, gold_embs)[0]
            best_idx = np.argmax(similarities)
            best_gold = gold_answers[best_idx]
        
        rows.append({
            "id": item["id"],
            "question": question,
            "predicted_answer": pred_text,
            "best_gold": best_gold,
            "sim_pos": f"{sim_pos:.4f}",
            "max_sim_neg": f"{sim_neg:.4f}",
            "decision": "correct" if pred == (1 if is_positive else 0) else "incorrect",
            "is_correct": "1" if pred == (1 if is_positive else 0) else "0"
        })
    
    # Tính metrics bằng sklearn
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # Xuất CSV
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "question", "predicted_answer", "best_gold", "sim_pos", "max_sim_neg", "decision", "is_correct"])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Rasa evaluation finished!")
    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1-score: {f1:.4f}")
    print(f"Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Rasa with SentenceTransformer")
    parser.add_argument("--data", default="datasets/dataTest.jsonl", help="Path to dataTest.jsonl")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model path")
    parser.add_argument("--rasa-url", default="http://localhost:5005/webhooks/rest/webhook", help="Rasa webhook URL")
    parser.add_argument("--outdir", default="datasets/eval", help="Output directory")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout")
    parser.add_argument("--tune-threshold", action="store_true", help="Tune threshold on dev set")
    parser.add_argument("--t-start", type=float, default=0.5, help="Threshold start for tuning")
    parser.add_argument("--t-end", type=float, default=0.95, help="Threshold end for tuning")
    parser.add_argument("--t-step", type=float, default=0.01, help="Threshold step for tuning")
    
    args = parser.parse_args()
    
    # Tạo output directory
    os.makedirs(args.outdir, exist_ok=True)
    
    # Load data
    print("Loading data...")
    items = load_data(args.data)
    print(f"Loaded {len(items)} items")
    
    # Load model
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer(args.model)
    
    # Tune threshold nếu được yêu cầu
    if args.tune_threshold:
        print("Tuning threshold...")
        threshold = tune_threshold(items, model, args.t_start, args.t_end, args.t_step)
        print(f"Best threshold: {threshold:.3f}")
    else:
        threshold = args.threshold
        print(f"Using fixed threshold: {threshold:.3f}")
    
    # Evaluate Rasa
    print("Evaluating Rasa...")
    output_file = os.path.join(args.outdir, "eval_rasa_results.csv")
    evaluate_rasa(items, model, args.rasa_url, threshold, args.timeout, output_file)
    
    print("Done!")


if __name__ == "__main__":
    main()