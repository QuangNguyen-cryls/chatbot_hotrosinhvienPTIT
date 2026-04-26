import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

# Attempt to import normalize_text if available; fall back to a no-op otherwise
try:
	from spelling import normalize_text as _normalize_text  # type: ignore
except Exception:
	def _normalize_text(text: str) -> str:  # type: ignore
		return " ".join(text.split())

# Global toggle for applying spelling.normalize_text
USE_SPELL_NORMALIZE: bool = False


def normalize_whitespace(text: str) -> str:
	"""Normalize spaces and fix trivial punctuation spacing issues without altering meaning."""
	text = text.replace("\u00A0", " ")  # non-breaking space
	text = re.sub(r"\s+", " ", text).strip()
	# Insert missing space after punctuation like '!H' -> '! H'
	text = re.sub(r"([!?.,;:])(\S)", r"\1 \2", text)
	# Collapse spaces before punctuation
	text = re.sub(r"\s+([!?.,;:])", r"\1", text)
	return text


def clean_text(text: str) -> str:
	# Apply optional spelling normalization only when explicitly enabled
	if USE_SPELL_NORMALIZE:
		text = _normalize_text(text)
	return normalize_whitespace(text)


HEADING_HINTS = (
	"A. ",
	"B. ",
	"C. ",
	"D. ",
	"Phần ",
	"Thẻ sinh viên",
	"Ký túc xá",
)


def is_heading(line: str) -> bool:
	l = line.strip()
	if not l:
		return False
	if any(l.startswith(h) for h in HEADING_HINTS):
		return True
	if re.match(r"^[A-D]\.\s", l):
		return True
	if re.match(r"^Phần\s+[IVXLC]+", l, re.IGNORECASE):
		return True
	# short descriptor lines ending with ':' and not Q/A/negative
	if (
		len(l) <= 60
		and l.endswith(":")
		and not re.match(r"^\s*(\d+\.)?\s*\.?Q\d*\s*:", l, re.IGNORECASE)
		and not re.match(r"^\s*-?\s*A\d*\s*:\s*", l, re.IGNORECASE)
		and not re.search(r"negative\s*\d*\s*:\s*", l, re.IGNORECASE)
		and not re.search(r"false\s*positive|false\s*negative|\bfb\b|\bfn\b", l, re.IGNORECASE)
	):
		return True
	# all-caps (rough heuristic for headings)
	letters = re.sub(r"[^A-Za-zÀ-ỹ\s]", "", l)
	if letters and letters.upper() == letters and len(l) <= 80:
		return True
	return False


R_Q = re.compile(r"^\s*(?:\d+\.)?\s*\.?Q\d*\s*:\s*(.+)$", re.IGNORECASE)
R_A = re.compile(r"^\s*-?\s*A\d*\s*:\s*(.+)$", re.IGNORECASE)
# Legacy negatives: A-negative n:
R_NEG1 = re.compile(r"^\s*[-•]?\s*(?:A-)?negative\s*(\d+)\s*:\s*(.+)$", re.IGNORECASE)
# New formats: FB 1:, False Positive 1:
R_NEG2 = re.compile(r"^\s*[-•]?\s*FB\s*(\d+)?\s*:\s*(.+)$", re.IGNORECASE)
R_NEG3 = re.compile(r"^\s*[-•]?\s*False\s*Positive\s*(\d+)?\s*:\s*(.+)$", re.IGNORECASE)
# FN / False Negative (no index expected):
R_NEG4 = re.compile(r"^\s*[-•]?\s*FN\s*:\s*(.+)$", re.IGNORECASE)
R_NEG5 = re.compile(r"^\s*[-•]?\s*False\s*Negative\s*:\s*(.+)$", re.IGNORECASE)


class QARecord:
	def __init__(self, idx: int, section: Optional[str]):
		self.idx: int = idx
		self.section: Optional[str] = section
		self.question: str = ""
		self.answer: str = ""
		self.negatives: List[str] = []
		self.meta_flags: List[str] = []  # parsing issues

	def to_json(self) -> Dict:
		obj = {
			"id": f"{self.idx:03d}",
			"section": self.section or "",
			"question": clean_text(self.question),
			"gold_answers": [clean_text(self.answer)] if self.answer else [],
			"negative_answers": [clean_text(n) for n in dedup(self.negatives)],
		}
		return obj


def dedup(items: List[str]) -> List[str]:
	seen = set()
	result: List[str] = []
	for it in items:
		key = it.strip().lower()
		if key and key not in seen:
			seen.add(key)
			result.append(it)
	return result


def parse_datatest(lines: List[str]) -> Tuple[List[QARecord], Dict[str, List[str]], List[str]]:
	"""Parse DataTest.txt lines into QA records and collect section negative pools.

	Returns (records, section_negative_pool, warnings)
	"""
	records: List[QARecord] = []
	section_negative_pool: Dict[str, List[str]] = {}
	warnings: List[str] = []

	current_section: Optional[str] = None
	current: Optional[QARecord] = None
	in_answer_block: bool = False

	for raw in lines:
		line = raw.rstrip("\n")
		# Skip file-level remarks but keep heuristics simple
		if not line.strip():
			# blank: allow answer continuation
			if in_answer_block and current is not None:
				current.answer += "\n"
			continue

		# Heading detection
		if is_heading(line) and not R_Q.match(line) and not R_A.match(line) and not (R_NEG1.match(line) or R_NEG2.match(line) or R_NEG3.match(line) or R_NEG4.match(line) or R_NEG5.match(line)):
			current_section = line.strip().rstrip(":")
			in_answer_block = False
			continue

		m_q = R_Q.match(line)
		if m_q:
			# finalize previous
			if current is not None and (current.question or current.answer or current.negatives):
				records.append(current)
			# start new QA
			current = QARecord(len(records) + 1, current_section)
			current.question = m_q.group(1).strip()
			in_answer_block = False
			continue

		m_a = R_A.match(line)
		if m_a:
			if current is None:
				# orphan A without Q
				current = QARecord(len(records) + 1, current_section)
				current.meta_flags.append("orphan_answer")
			current.answer = m_a.group(1).strip()
			in_answer_block = True
			continue

		# Negatives (multiple formats)
		m = R_NEG1.match(line)
		if not m:
			m = R_NEG2.match(line)
		if not m:
			m = R_NEG3.match(line)
		if m:
			if current is None:
				warnings.append(f"Negative without Q at: {line[:80]}")
				continue
			neg_text = m.group(2).strip() if m.lastindex and m.lastindex >= 2 else ""
			if neg_text:
				current.negatives.append(neg_text)
				key = (current.section or "").strip()
				if key:
					section_negative_pool.setdefault(key, []).append(neg_text)
			in_answer_block = False
			continue

		m4 = R_NEG4.match(line)
		m5 = None if m4 else R_NEG5.match(line)
		if m4 or m5:
			if current is None:
				warnings.append(f"Negative without Q at: {line[:80]}")
				continue
			neg_text = (m4.group(1) if m4 else m5.group(1)).strip()
			if neg_text:
				current.negatives.append(neg_text)
				key = (current.section or "").strip()
				if key:
					section_negative_pool.setdefault(key, []).append(neg_text)
			in_answer_block = False
			continue

		# Continuation lines
		if in_answer_block and current is not None:
			# append to current answer text
			current.answer += (" " if current.answer and not current.answer.endswith("\n") else "") + line.strip()
			continue

		# Unrecognized line: could be list bullets or extra info; attach to answer if exists, else skip
		if current is not None and current.answer:
			current.answer += (" " if not current.answer.endswith("\n") else "") + line.strip()
			continue

		# Otherwise, ignore but warn
		warnings.append(f"Unparsed line: {line[:80]}")

	# finalize last
	if current is not None and (current.question or current.answer or current.negatives):
		records.append(current)

	# Normalize and clean pools
	for sec, arr in list(section_negative_pool.items()):
		section_negative_pool[sec] = dedup([clean_text(x) for x in arr])

	return records, section_negative_pool, warnings


def generate_near_negatives(answer: str, max_generate: int = 2) -> List[str]:
	"""Generate simple near-negative variants from the answer by negating leading affirmations
	and perturbing numeric values. This is heuristic and conservative.
	"""
	candidates: List[str] = []
	ans = answer.strip()
	if not ans:
		return candidates

	# Negate leading 'Có' or 'Có.' / 'Có!'
	if re.match(r"^(Có\b|Có[.!])", ans, re.IGNORECASE):
		candidates.append(re.sub(r"^Có\b[\.!]?\s*", "Không ", ans, flags=re.IGNORECASE))

	# If answer has 'Không', flip to 'Có' (rare but gives a contrast)
	elif re.match(r"^(Không\b|Không[.!])", ans, re.IGNORECASE):
		candidates.append(re.sub(r"^Không\b[\.!]?\s*", "Có ", ans, flags=re.IGNORECASE))

	# Numeric perturbation: change percentages or integers slightly
	def _bump_number(m: re.Match) -> str:
		val = m.group(0)
		# Remove separators for a safe parse
		num = re.sub(r"[^0-9]", "", val)
		if not num:
			return val
		n = int(num)
		bumped = max(0, n + 10 if n < 1000 else int(n * 1.1))
		return val.replace(num, str(bumped))

	if re.search(r"\d", ans):
		candidates.append(re.sub(r"\d[\d.,%]*", _bump_number, ans, count=1))

	# Slight modality change
	if len(candidates) < max_generate:
		candidates.append("Thông tin trên không áp dụng trong trường hợp này theo quy định hiện hành.")

	return candidates[:max_generate]


def autofill_negatives(records: List[QARecord], section_pool: Dict[str, List[str]], min_neg: int = 3, max_neg: int = 5) -> Tuple[int, int]:
	"""Ensure each QA has at least min_neg negatives by borrowing from section pools and generating near-negatives.
	Returns (num_filled, total_added)
	"""
	num_filled = 0
	total_added = 0
	for rec in records:
		existing = dedup(rec.negatives)
		added: List[str] = []
		# Borrow from section pool
		sec_key = (rec.section or "").strip()
		if sec_key and sec_key in section_pool:
			for cand in section_pool[sec_key]:
				if len(existing) + len(added) >= min_neg:
					break
				if cand.lower() not in {x.lower() for x in existing + added}:
					added.append(cand)

		# Generate near-negatives based on answer
		if len(existing) + len(added) < min_neg and rec.answer:
			for gen in generate_near_negatives(rec.answer, max_generate=3):
				if len(existing) + len(added) >= min_neg:
					break
				if gen.lower() not in {x.lower() for x in existing + added}:
					added.append(gen)

		# If still lacking, borrow generic negatives from all pools
		if len(existing) + len(added) < min_neg:
			for _, pool in section_pool.items():
				for cand in pool:
					if len(existing) + len(added) >= min_neg:
						break
					if cand.lower() not in {x.lower() for x in existing + added}:
						added.append(cand)
				if len(existing) + len(added) >= min_neg:
					break

		if added:
			rec.negatives = dedup((existing + added)[:max_neg])
			num_filled += 1
			total_added += len(added)
		else:
			rec.negatives = existing[:max_neg]

	return num_filled, total_added


def write_jsonl(records: List[QARecord], out_path: str) -> None:
	with open(out_path, "w", encoding="utf-8") as f:
		for rec in records:
			obj = rec.to_json()
			f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def write_report(records: List[QARecord], warnings: List[str], filled_stats: Tuple[int, int], report_path: str) -> None:
	n_total = len(records)
	n_no_answer = sum(1 for r in records if not r.answer)
	n_no_question = sum(1 for r in records if not r.question)
	n_low_neg = sum(1 for r in records if len(r.negatives) < 3)

	n_filled, total_added = filled_stats

	lines: List[str] = []
	lines.append("# DataTest Normalization Report\n")
	lines.append(f"- Total items: {n_total}")
	lines.append(f"- Items missing answer: {n_no_answer}")
	lines.append(f"- Items missing question: {n_no_question}")
	lines.append(f"- Items with <3 negatives AFTER fill: {n_low_neg}")
	lines.append(f"- Items auto-filled negatives: {n_filled} (added {total_added} negatives)\n")

	lines.append("## Sample issues\n")
	for w in warnings[:50]:
		lines.append(f"- {w}")
	if len(warnings) > 50:
		lines.append(f"- ... and {len(warnings) - 50} more")

	lines.append("\n## Items needing attention (<3 negatives or missing fields)\n")
	for rec in records:
		if (len(rec.negatives) < 3) or (not rec.question) or (not rec.answer):
			lines.append(f"- id={rec.idx:03d} section='{rec.section or ''}' q_missing={not bool(rec.question)} a_missing={not bool(rec.answer)} neg_count={len(rec.negatives)}")

	with open(report_path, "w", encoding="utf-8") as f:
		f.write("\n".join(lines))


def main(argv: List[str]) -> int:
	import argparse
	parser = argparse.ArgumentParser(description="Normalize DataTest.txt into JSONL with Q/A/negatives and sections")
	parser.add_argument("--input", default=os.path.join("datasets", "DataTest.txt"))
	parser.add_argument("--output", default=os.path.join("datasets", "dataTest.jsonl"))
	parser.add_argument("--report", default=os.path.join("datasets", "dataTest_report.md"))
	parser.add_argument("--use-spell-normalize", action="store_true", help="Apply spelling.normalize_text before whitespace cleanup")
	args = parser.parse_args(argv)

	# set global toggle
	global USE_SPELL_NORMALIZE
	USE_SPELL_NORMALIZE = bool(args.use_spell_normalize)

	if not os.path.exists(args.input):
		print(f"Input not found: {args.input}", file=sys.stderr)
		return 1

	with open(args.input, "r", encoding="utf-8") as f:
		lines = f.readlines()

	records, section_pool, warnings = parse_datatest(lines)

	# Clean texts and dedup negatives per record
	for rec in records:
		rec.question = clean_text(rec.question)
		rec.answer = clean_text(rec.answer)
		rec.negatives = dedup([clean_text(n) for n in rec.negatives])

	filled_stats = autofill_negatives(records, section_pool, min_neg=3, max_neg=5)

	os.makedirs(os.path.dirname(args.output), exist_ok=True)
	write_jsonl(records, args.output)
	write_report(records, warnings, filled_stats, args.report)

	print(f"Wrote JSONL: {args.output}")
	print(f"Wrote report: {args.report}")
	print(f"Items: {len(records)}")
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
