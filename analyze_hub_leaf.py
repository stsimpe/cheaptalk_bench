"""
Hub vs Leaf influence analysis (RQ2) on existing star-topology runs.

Computes, per model x game x condition:
  1. Hub vs leaf cooperation rates
  2. Lead-lag influence:  Delta(hub->leaf)  vs  Delta(leaf->hub)
  3. Defection cascades from full-cooperation rounds (hub-initiated vs leaf-initiated)
  4. P(run converges to cooperation | hub's round-1 action)

Usage:  python analyze_hub_leaf.py
Output: hub_leaf_summary.csv + console report
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------- config
MODELS = {
    "Qwen2.5-7B":  r"C:\Users\tsimp\OneDrive\Υπολογιστής\diplomatikh\run1_qwen2.5_7b",
    "Qwen3-4B":    r"C:\Users\tsimp\OneDrive\Υπολογιστής\diplomatikh\run2_qwen3_4b",
    "Gemma-2-2B":  r"C:\Users\tsimp\OneDrive\Υπολογιστής\diplomatikh\run_3_gemma_2_2b_it",
    "Gemma-2-9B":  r"C:\Users\tsimp\OneDrive\Υπολογιστής\diplomatikh\run_4_gemma_2_9b_it",
    "Llama-3.1-8B": r"C:\Users\tsimp\OneDrive\Υπολογιστής\diplomatikh\run5_llama_3.1_8b_instruct",
}
COOP_ACTIONS = {"Cooperate", "Stag"}
OUT_CSV = Path(__file__).parent / "hub_leaf_summary.csv"

# ---------------------------------------------------------------- loading

def condition_label(cfg):
    """Robust condition label from the JSON config itself (not folder names)."""
    if cfg.get("condition") == "no_comm":
        return "no_comm"
    pol = cfg.get("message_policy", "meaningful")
    frm = cfg.get("framing_type", "neutral")
    if frm and frm != "neutral":
        return f"framing_{frm}".replace("framing_framing_", "framing_")
    if pol == "meaningful":
        return "cheap_talk"
    return pol  # silence / no_sense / counterfactual ...


def load_runs(root):
    """Yield deduplicated run dicts. Dedupe key uses config + run_id + game,
    which collapses the duplicated results/ subfolder copies in run_3."""
    seen = set()
    for p in sorted(Path(root).rglob("*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except (json.JSONDecodeError, OSError):
            print(f"  [skip unreadable] {p}")
            continue
        if "history" not in d or "config" not in d:
            continue
        cfg = d["config"]
        cond = condition_label(cfg)
        key = (cfg.get("game"), cond, d.get("run_id"),
               len(d["history"]), p.name)
        if key in seen:
            continue
        seen.add(key)
        yield cond, cfg.get("game", "?"), d


# ---------------------------------------------------------------- per-run metrics

def run_metrics(d):
    hub = str(d["topology"]["hub_id"])
    agents = [str(a) for a in range(d["topology"]["n_agents"])]
    leaves = [a for a in agents if a != hub]
    hist = d["history"]

    coop = lambda r, a: r["actions"].get(a) in COOP_ACTIONS
    valid = lambda r, a: not r.get("invalid", {}).get(a, False)

    m = defaultdict(int)

    # 1. cooperation rates (valid actions only)
    for r in hist:
        for a in agents:
            if not valid(r, a):
                continue
            tgt = "hub" if a == hub else "leaf"
            m[f"{tgt}_n"] += 1
            m[f"{tgt}_coop"] += coop(r, a)

    # 2. lead-lag transitions
    for t in range(len(hist) - 1):
        r0, r1 = hist[t], hist[t + 1]
        if valid(r0, hub):
            h0 = coop(r0, hub)
            for lf in leaves:
                if valid(r1, lf):
                    m[f"leaf1_given_hub{int(h0)}_n"] += 1
                    m[f"leaf1_given_hub{int(h0)}_coop"] += coop(r1, lf)
        lv = [coop(r0, lf) for lf in leaves if valid(r0, lf)]
        if lv and valid(r1, hub):
            maj = int(sum(lv) * 2 >= len(lv))  # leaf majority cooperative?
            m[f"hub1_given_leaf{maj}_n"] += 1
            m[f"hub1_given_leaf{maj}_coop"] += coop(r1, hub)

    # 3. cascades: from a fully cooperative round t, single defector at t -> ...
    for t in range(len(hist) - 1):
        r0, r1 = hist[t], hist[t + 1]
        acts0 = {a: coop(r0, a) for a in agents if valid(r0, a)}
        if len(acts0) < len(agents):
            continue
        defectors = [a for a, c in acts0.items() if not c]
        if len(defectors) != 1:
            continue
        src = "hub" if defectors[0] == hub else "leaf"
        others = [a for a in agents if a != defectors[0] and valid(r1, a)]
        if others:
            m[f"cascade_{src}_n"] += len(others)
            m[f"cascade_{src}_defect"] += sum(not coop(r1, a) for a in others)

    # 4. hub round-1 action vs final outcome (last 4 rounds all-coop?)
    if hist and valid(hist[0], hub):
        h1 = int(coop(hist[0], hub))
        tail = hist[-4:]
        conv = all(coop(r, a) for r in tail for a in agents if valid(r, a))
        m[f"conv_given_hub1_{h1}_n"] += 1
        m[f"conv_given_hub1_{h1}_yes"] += int(conv)

    return m


# ---------------------------------------------------------------- aggregate

def pct(num, den):
    return round(100 * num / den, 1) if den else None


def main():
    agg = defaultdict(lambda: defaultdict(int))
    for model, root in MODELS.items():
        if not Path(root).exists():
            print(f"[missing folder] {root}")
            continue
        n = 0
        for cond, game, d in load_runs(root):
            mm = run_metrics(d)
            key = (model, game, cond)
            for k, v in mm.items():
                agg[key][k] += v
            n += 1
        print(f"{model}: {n} runs loaded")

    rows = []
    for (model, game, cond), m in sorted(agg.items()):
        hub_c = pct(m["hub_coop"], m["hub_n"])
        leaf_c = pct(m["leaf_coop"], m["leaf_n"])
        p_l_h1 = pct(m["leaf1_given_hub1_coop"], m["leaf1_given_hub1_n"])
        p_l_h0 = pct(m["leaf1_given_hub0_coop"], m["leaf1_given_hub0_n"])
        p_h_l1 = pct(m["hub1_given_leaf1_coop"], m["hub1_given_leaf1_n"])
        p_h_l0 = pct(m["hub1_given_leaf0_coop"], m["hub1_given_leaf0_n"])
        d_hl = round(p_l_h1 - p_l_h0, 1) if None not in (p_l_h1, p_l_h0) else None
        d_lh = round(p_h_l1 - p_h_l0, 1) if None not in (p_h_l1, p_h_l0) else None
        rows.append({
            "model": model, "game": game, "condition": cond,
            "hub_coop_%": hub_c, "leaf_coop_%": leaf_c,
            "P(leaf C | hub C)": p_l_h1, "P(leaf C | hub D)": p_l_h0,
            "influence_hub->leaf": d_hl,
            "P(hub C | leaves C)": p_h_l1, "P(hub C | leaves D)": p_h_l0,
            "influence_leaf->hub": d_lh,
            "cascade_after_hub_defect_%": pct(m["cascade_hub_defect"], m["cascade_hub_n"]),
            "cascade_after_leaf_defect_%": pct(m["cascade_leaf_defect"], m["cascade_leaf_n"]),
            "P(converge | hub1=C)": pct(m["conv_given_hub1_1_yes"], m["conv_given_hub1_1_n"]),
            "P(converge | hub1=D)": pct(m["conv_given_hub1_0_yes"], m["conv_given_hub1_0_n"]),
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {len(rows)} rows -> {OUT_CSV}\n")

    # console highlights: where hub->leaf influence beats leaf->hub
    print(f"{'model':14} {'game':4} {'condition':20} {'hub→leaf':>9} {'leaf→hub':>9}")
    for r in rows:
        a, b = r["influence_hub->leaf"], r["influence_leaf->hub"]
        if a is not None and b is not None:
            flag = "  <== hub drives" if a - b >= 15 else ""
            print(f"{r['model']:14} {r['game']:4} {r['condition']:20} {a:9} {b:9}{flag}")


if __name__ == "__main__":
    main()