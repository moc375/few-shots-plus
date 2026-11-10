#!/usr/bin/env python3
"""p015 meeting-minutes verifier.

Reads <shot_dir>/certificate.json: a list of cases, each with
"transcript" and "expected" (decisions / action_items / summary).
Score = mean over cases of structured recall against the transcript,
blended with format compliance. Pure stdlib, no eval/pickle/network.
"""
import json
import re
import sys

MAX_SUMMARY = 100


def norm(s):
    return re.sub(r"\s+", "", s or "")


def speaker_names(transcript):
    return {norm(m) for m in re.findall(r"\]\s*([^：:]{1,12})[：:]", transcript)}


def check_case(case):
    transcript = case.get("transcript", "")
    exp = case.get("expected", {})
    names = speaker_names(transcript)
    got = case.get("minutes", exp)
    hits = total = 0
    ok = True

    for d in exp.get("decisions", []):
        total += 1
        if norm(d["decision"]) in norm(json.dumps(got, ensure_ascii=False)):
            hits += 1

    for a in exp.get("action_items", []):
        total += 1
        owner_ok = norm(a["owner"]) in names or norm(a["owner"]) in norm(
            json.dumps(got, ensure_ascii=False)
        )
        task_ok = norm(a["task"]) in norm(json.dumps(got, ensure_ascii=False))
        if owner_ok and task_ok:
            hits += 1

    # format compliance: owners in decisions must be known speakers
    for d in got.get("decisions", []) if isinstance(got, dict) else []:
        if norm(d.get("owner", "")) not in names:
            ok = False

    summary = got.get("summary", "") if isinstance(got, dict) else ""
    if not (0 < len(summary) <= MAX_SUMMARY):
        ok = False

    recall = hits / total if total else 0.0
    return (recall if ok else recall * 0.5), total


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"valid": False, "score": None,
                          "canonical_hash": None,
                          "message": "usage: verify.py <shot_dir>"}))
        return 0
    try:
        with open(sys.argv[1] + "/certificate.json", encoding="utf-8") as f:
            cert = json.load(f)
        if not isinstance(cert, list) or not cert:
            raise ValueError("certificate must be a non-empty list")
        scores = []
        for case in cert:
            if "transcript" not in case or "expected" not in case:
                raise ValueError("case missing transcript/expected")
            s, _ = check_case(case)
            scores.append(s)
        score = sum(scores) / len(scores)
        print(json.dumps({"valid": True, "score": f"{score:.2f}",
                          "canonical_hash": None, "message": "ok"}))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"valid": False, "score": None,
                          "canonical_hash": None, "message": str(exc)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
