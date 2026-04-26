import os
import argparse
from pathlib import Path
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer, losses, datasets, models
from torch.utils.data import DataLoader

from data_processor import (
    build_dataset_from_handbook,
    load_input_examples,
    get_corpus_sentences,
)
import faiss
from spelling import normalize_text


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_HANDBOOK = str(BASE_DIR / "handbook_summary.txt")
OUTPUT_DIR = BASE_DIR / "models" / "ptit-sbert"


def build_model(model_name: str = "distiluse-base-multilingual-cased-v2") -> SentenceTransformer:
    """
    Khởi tạo SentenceTransformer theo sơ đồ đã thiết kế:
    - Tokenization và Embedding sẽ do backbone model đảm nhiệm
    - Encoder: Transformer + MeanPooling
    """
    # Sử dụng pipeline dựng sẵn của SentenceTransformer với MeanPooling head
    return SentenceTransformer(model_name)


def train_sentence_transformer(
    handbook_path: str = DEFAULT_HANDBOOK,
    base_model: str = "distiluse-base-multilingual-cased-v2",
    epochs: int = 1,
    batch_size: int = 32,
    learning_rate: float = 2e-5,
    warmup_steps: int | None = None,
) -> SentenceTransformer:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1) Build dataset (pairs) from handbook
    jsonl_path = build_dataset_from_handbook(handbook_path)
    train_examples = load_input_examples(jsonl_path)

    # 2) Model
    model = build_model(base_model)

    # 3) DataLoader & Loss (MultipleNegativesRankingLoss for STS-style training)
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    # 4) Warmup steps
    if warmup_steps is None:
        warmup_steps = int(len(train_dataloader) * epochs * 0.1)

    # 5) Fit
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=warmup_steps,
        optimizer_params={"lr": learning_rate},
        output_path=str(OUTPUT_DIR),
        show_progress_bar=True,
    )

    return model


def embed_corpus(model: SentenceTransformer, handbook_path: str = DEFAULT_HANDBOOK) -> tuple[List[str], np.ndarray]:
    sentences = get_corpus_sentences(handbook_path)
    embeddings = model.encode(sentences, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)
    return sentences, embeddings


def save_index(sentences: List[str], embeddings: np.ndarray, out_dir: Path = OUTPUT_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)
    np.save(out_dir / "corpus_embeddings.npy", embeddings)
    with open(out_dir / "corpus_sentences.txt", "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(s + "\n")
    # FAISS index (Inner Product on normalized embeddings == cosine similarity)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings.astype(np.float32))
    faiss.write_index(index, str(out_dir / "faiss_index.idx"))


def load_index(out_dir: Path = OUTPUT_DIR) -> tuple[List[str], faiss.Index]:
    with open(out_dir / "corpus_sentences.txt", "r", encoding="utf-8") as f:
        sentences = [line.rstrip("\n") for line in f]
    index = faiss.read_index(str(out_dir / "faiss_index.idx"))
    return sentences, index


def query(model: SentenceTransformer, user_query: str, top_k: int = 5,
          out_dir: Path = OUTPUT_DIR) -> List[tuple[float, str]]:
    sentences, index = load_index(out_dir)
    q_emb = model.encode([user_query], convert_to_numpy=True, normalize_embeddings=True)
    scores, idxs = index.search(q_emb.astype(np.float32), top_k)
    results: List[tuple[float, str]] = []
    for score, idx in zip(scores[0], idxs[0]):
        results.append((float(score), sentences[int(idx)]))
    return results


def compose_context(sentences: List[str], pivot_index: int, window: int = 1) -> str:
    start = max(0, pivot_index - window)
    end = min(len(sentences), pivot_index + window + 1)
    return " ".join(sentences[start:end])


class PreciseHandbookChatbot:
    """
    Lớp bao đóng để dùng trong main.py
    - load_model(): nạp model đã train hoặc base model
    - load_index(): nạp FAISS index và corpus; trả về True/False
    - parse_handbook_precise(path): trả về danh sách câu đã làm sạch
    - create_embeddings(chunks): tính embedding và lưu index
    - answer_question_precise(text): truy vấn KB với ngưỡng và trả lời gộp ngữ cảnh
    """

    def __init__(
        self,
        model_dir: str | Path = OUTPUT_DIR,
        handbook_path: str = DEFAULT_HANDBOOK,
        threshold: float = 0.7,
        top_k: int = 5,
        window: int = 2,
        keyword_boost: float = 0.1,
        use_normalize: bool = True,
    ) -> None:
        self.model_dir = Path(model_dir)
        self.handbook_path = handbook_path
        self.threshold = threshold
        self.top_k = top_k
        self.window = window
        self.keyword_boost = keyword_boost
        self.use_normalize = use_normalize
        self.model: SentenceTransformer | None = None

    # Model
    def load_model(self) -> None:
        if self.model_dir.is_dir() and (self.model_dir / "config.json").exists():
            self.model = SentenceTransformer(str(self.model_dir))
        else:
            self.model = build_model()

    # Index
    def load_index(self) -> bool:
        if (self.model_dir / "faiss_index.idx").exists() and (self.model_dir / "corpus_sentences.txt").exists():
            return True
        return False

    # Data parsing
    def parse_handbook_precise(self, path: str | None = None) -> List[str]:
        return get_corpus_sentences(path or self.handbook_path)

    # Build embeddings and save index
    def create_embeddings(self, sentences: List[str] | None = None) -> None:
        if self.model is None:
            self.load_model()
        assert self.model is not None
        sents = sentences or get_corpus_sentences(self.handbook_path)
        embs = self.model.encode(sents, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)
        save_index(sents, embs, out_dir=self.model_dir)

    # Answer
    def answer_question_precise(self, user_text: str) -> str:
        if self.model is None:
            self.load_model()
        assert self.model is not None

        # Ensure KB exists
        if not self.load_index():
            self.create_embeddings()

        sentences, index = load_index(self.model_dir)

        # Expand queries similar to CLI
        queries = expand_query_variants(user_text, self.use_normalize)
        ranked = rank_candidates(self.model, sentences, index, queries, self.top_k, self.keyword_boost, base_query=queries[0])

        # Compose answer
        for idx, score in ranked:
            if score >= self.threshold:
                context = compose_context(sentences, int(idx), window=self.window)
                return context
        return "Không tìm thấy thông tin đủ tin cậy trong kho tri thức. Hãy hỏi cụ thể hơn."


def expand_query_variants(raw_query: str, use_normalize: bool = True) -> List[str]:
    q_norm = raw_query if not use_normalize else normalize_text(raw_query)
    expansions_map = {
        "tầm nhìn": ["tầm nhìn", "vision"],
        "sứ mệnh": ["sứ mệnh", "sứ mạng", "mission"],
        "giá trị cốt lõi": ["giá trị cốt lõi", "core values"],
        "lịch sử hình thành và phát triển": ["lịch sử", "hình thành và phát triển", "history"],
    }
    expanded_queries: List[str] = [q_norm]
    for key, variants in expansions_map.items():
        if key in q_norm:
            expanded_queries = list(dict.fromkeys(expanded_queries + variants))
            break
    return expanded_queries


def rank_candidates(model: SentenceTransformer, sentences: List[str], index: faiss.Index, queries: List[str],
                    top_k: int, keyword_boost: float, base_query: str) -> List[tuple[int, float]]:
    # Search for each expansion and keep best scores per index
    best_scores: dict[int, float] = {}
    for q in queries:
        q_emb = model.encode([q], convert_to_numpy=True, normalize_embeddings=True)
        scores, idxs = index.search(q_emb.astype(np.float32), max(20, top_k))
        for score, idx in zip(scores[0], idxs[0]):
            idx = int(idx)
            score = float(score)
            if idx not in best_scores or score > best_scores[idx]:
                best_scores[idx] = score

    # Keyword boosting using base_query tokens
    keywords = [w for w in base_query.lower().split() if len(w) >= 3]
    for idx, score in list(best_scores.items()):
        text = sentences[idx].lower()
        if any(k in text for k in keywords):
            best_scores[idx] = score + float(keyword_boost)

    ranked = sorted(best_scores.items(), key=lambda x: x[1], reverse=True)[: top_k]
    return ranked


def main():
    parser = argparse.ArgumentParser(description="Train SBERT, build knowledge base, and query.")
    parser.add_argument("--train", action="store_true", help="Train the SentenceTransformer before building KB.")
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Training learning rate")
    parser.add_argument("--handbook", type=str, default=DEFAULT_HANDBOOK, help="Path to handbook_summary.txt")
    parser.add_argument("--model-path", type=str, default=str(OUTPUT_DIR), help="Directory of trained model to use.")
    parser.add_argument("--build-kb-only", action="store_true", help="Only build KB using the model at --model-path (skip training).")
    parser.add_argument("--query", type=str, default=None, help="Run a sample query against the KB.")
    parser.add_argument("--top-k", type=int, default=5, help="Top K results to return for --query.")
    parser.add_argument("--threshold", type=float, default=0.7, help="Confidence threshold for accepting an answer.")
    parser.add_argument("--window", type=int, default=2, help="Number of neighboring sentences to include as context.")
    parser.add_argument("--use-base", action="store_true", help="Force using the base pretrained model for inference.")
    parser.add_argument("--no-normalize", action="store_true", help="Do not normalize user query text.")
    parser.add_argument("--keyword-boost", type=float, default=0.1, help="Add this value to score if candidate contains important keywords.")

    args = parser.parse_args()

    model: SentenceTransformer

    if args.train:
        model = train_sentence_transformer(
            handbook_path=args.handbook,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
        )
    else:
        # Load existing trained model or base model if not found
        if not args.use_base and os.path.isdir(args.model_path) and (Path(args.model_path) / "config.json").exists():
            model = SentenceTransformer(args.model_path)
        else:
            model = build_model()

    if args.train or args.build_kb_only:
        sents, embs = embed_corpus(model, handbook_path=args.handbook)
        save_index(sents, embs)
        print(f"Knowledge base built at: {OUTPUT_DIR}")

    if args.query is not None:
        # Ensure KB exists; if not, build quickly
        if not (OUTPUT_DIR / "faiss_index.idx").exists():
            sents, embs = embed_corpus(model, handbook_path=args.handbook)
            save_index(sents, embs)
            print(f"Knowledge base built at: {OUTPUT_DIR}")

        sentences, index = load_index(OUTPUT_DIR)

        # Normalize and expand query
        raw_q = args.query
        q_norm = raw_q if args.no_normalize else normalize_text(raw_q)
        expansions_map = {
            "tầm nhìn": ["tầm nhìn", "vision"],
            "sứ mệnh": ["sứ mệnh", "sứ mạng", "mission"],
            "giá trị cốt lõi": ["giá trị cốt lõi", "core values"],
            "lịch sử hình thành và phát triển": ["lịch sử", "hình thành và phát triển", "history"],
        }
        expanded_queries: List[str] = [q_norm]
        for key, variants in expansions_map.items():
            if key in q_norm:
                expanded_queries = list(dict.fromkeys(expanded_queries + variants))
                break

        # Search for each expansion and keep best scores
        best_scores = {}
        best_idxs = {}
        for q in expanded_queries:
            q_emb = model.encode([q], convert_to_numpy=True, normalize_embeddings=True)
            scores, idxs = index.search(q_emb.astype(np.float32), max(20, args.top_k))
            for score, idx in zip(scores[0], idxs[0]):
                idx = int(idx)
                score = float(score)
                if idx not in best_scores or score > best_scores[idx]:
                    best_scores[idx] = score
                    best_idxs[idx] = idx

        # Keyword boosting
        keywords = [w for w in q_norm.split() if len(w) >= 3]
        for idx, score in list(best_scores.items()):
            text = sentences[idx].lower()
            if any(k in text for k in keywords):
                best_scores[idx] = score + float(args.keyword_boost)

        # Rank and take top-k
        ranked = sorted(best_scores.items(), key=lambda x: x[1], reverse=True)[: args.top_k]

        print("Top results:")
        accepted_any = False
        for rank, (idx, score) in enumerate(ranked, start=1):
            text = sentences[idx]
            print(f"{rank}. score={float(score):.3f} | {text}")
            if not accepted_any and float(score) >= args.threshold:
                accepted_any = True
                context = compose_context(sentences, int(idx), window=args.window)
                print("\nAnswer (auto-composed):")
                print(context)
        if not accepted_any:
            print("\nAnswer: Không tìm thấy thông tin đủ tin cậy trong kho tri thức (score < threshold). Hãy đặt câu hỏi cụ thể hơn hoặc tăng --window.")


if __name__ == "__main__":
    main()


