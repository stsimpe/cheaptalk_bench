"""Agent: holds state (position in topology, view of history) and calls the LLM.

The agent does NOT hold its own full history list — history is owned by the
engine and passed in per decision, because on a star the hub's view differs
from a leaf's view and we want that filtering to live in one place (the engine).

JSON parsing strategy:
  Models occasionally produce output that is "almost JSON" — most commonly,
  literal newlines inside string values, which strictly speaking is invalid
  JSON. We try four strategies in increasing order of leniency:
    1. Standard json.loads
    2. Extract first {...} block, then json.loads
    3. Auto-repair: escape unescaped newlines inside string values
    4. Last-resort regex: pull "action" field directly from the text
  If all four fail, we return a sentinel that the engine will mark as invalid
  (so the run continues — one bad parse doesn't kill the experiment).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from games import Game
from llm_client import LLMClient
from message_policies import apply_policy, MessagePolicy
from prompts import (
    build_system_prompt,
    build_no_comm_user,
    build_ct_communicate_user,
    build_ct_action_user,
    format_history,
)


JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
ACTION_FIELD_RE = re.compile(r'"action"\s*:\s*"([^"]+)"', re.IGNORECASE)
MESSAGE_FIELD_RE = re.compile(r'"message"\s*:\s*"([^"]+)"', re.IGNORECASE)


def _repair_unescaped_newlines(text: str) -> str:
    """Escape literal \\n / \\r characters that appear INSIDE JSON string values.

    The model sometimes emits raw newlines inside long reasoning fields, e.g.

        {"reasoning": "first line
        second line", "action": "Cooperate"}

    which is invalid JSON. We walk the string, track whether we're inside a
    "..." string literal, and replace newlines with their escaped forms.
    """
    out: list[str] = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            out.append(ch)
            escape_next = False
            continue
        if ch == "\\" and in_string:
            out.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch == "\n":
            out.append("\\n")
            continue
        if in_string and ch == "\r":
            out.append("\\r")
            continue
        if in_string and ch == "\t":
            out.append("\\t")
            continue
        out.append(ch)
    return "".join(out)


def extract_json(text: str) -> dict:
    """Robust JSON extraction with multiple fallbacks.

    Raises ValueError only if even the regex-based field extraction fails.
    """
    # Strategy 1: standard parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract first {...} block
    m = JSON_BLOCK_RE.search(text)
    if m:
        block = m.group(0)
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            pass

        # Strategy 3: auto-repair unescaped control chars inside the block
        repaired = _repair_unescaped_newlines(block)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    # Strategy 4: last-resort regex on raw text
    action_match = ACTION_FIELD_RE.search(text)
    message_match = MESSAGE_FIELD_RE.search(text)
    if action_match or message_match:
        result: dict = {"reasoning": "[unparseable JSON; fields recovered via regex]"}
        if action_match:
            result["action"] = action_match.group(1)
        if message_match:
            result["message"] = message_match.group(1)
        return result

    raise ValueError(f"Could not parse JSON from model output:\n{text}")


@dataclass
class Agent:
    agent_id: int
    n_neighbors: int
    neighbor_ids: list[int]
    total_agents: int
    game: Game
    condition: str              # "no_comm" or "cheap_talk"
    client: LLMClient
    message_max_words: int = 20
    memory_window: int = 10     # Sabani §4.1.4: sliding window length
    message_policy: MessagePolicy = "meaningful"  # ablation control

    def _system_prompt(self) -> str:
        return build_system_prompt(
            game=self.game,
            condition=self.condition,
            n_neighbors=self.n_neighbors,
            total_agents=self.total_agents,
            message_max_words=self.message_max_words,
        )

    def _history_text(self, history: list[dict]) -> str:
        return format_history(
            history, self.agent_id, self.neighbor_ids,
            memory_window=self.memory_window,
        )

    def _safe_extract(self, raw: str, expected_field: str) -> tuple[dict, bool]:
        """Try to parse JSON; if it fails, return a sentinel and True for `failed`.

        The engine treats failed parses as invalid actions but does NOT crash.
        """
        try:
            parsed = extract_json(raw)
            return parsed, False
        except ValueError as e:
            print(f"    [parse error] agent {self.agent_id}: {e}")
            return {"reasoning": "[unparseable]", expected_field: ""}, True

    # --- No-communication path ---

    def choose_action_no_comm(self, history: list[dict], round_num: int) -> tuple[str, str]:
        user = build_no_comm_user(self._history_text(history), round_num)
        raw = self.client.generate(self._system_prompt(), user)
        parsed, _failed = self._safe_extract(raw, "action")
        action = str(parsed.get("action", "")).strip()
        reasoning = str(parsed.get("reasoning", ""))
        return self._canonicalize_action(action), reasoning

    # --- Cheap-talk path ---

    def send_message(self, history: list[dict], round_num: int) -> tuple[str, str]:
        # Skip the LLM call entirely when policy doesn't use its output
        if self.message_policy in ("irrelevant", "silence"):
            return apply_policy(self.message_policy, self.agent_id, round_num, ""), ""

        user = build_ct_communicate_user(self._history_text(history), round_num)
        raw = self.client.generate(self._system_prompt(), user)
        parsed, _failed = self._safe_extract(raw, "message")
        llm_message = str(parsed.get("message", "")).strip()
        reasoning = str(parsed.get("reasoning", ""))

        words = llm_message.split()
        if len(words) > self.message_max_words:
            llm_message = " ".join(words[: self.message_max_words])

        return apply_policy(self.message_policy, self.agent_id, round_num, llm_message), reasoning

    def choose_action_cheap_talk(
        self,
        history: list[dict],
        round_num: int,
        own_message: str,
        received_messages: dict[int, str],
    ) -> tuple[str, str]:
        user = build_ct_action_user(
            self._history_text(history), round_num, own_message, received_messages
        )
        raw = self.client.generate(self._system_prompt(), user)
        parsed, _failed = self._safe_extract(raw, "action")
        action = str(parsed.get("action", "")).strip()
        reasoning = str(parsed.get("reasoning", ""))
        return self._canonicalize_action(action), reasoning

    # --- Helpers ---

    def _canonicalize_action(self, raw: str) -> str:
        """Map any reasonable variation to one of the canonical action labels.

        Invalid responses are returned as-is and flagged by the engine; we do
        NOT silently substitute because invalid-rate is a metric we care about
        (following Sabani §4.1.4).
        """
        a, b = self.game.action_labels
        low = raw.lower().strip().strip(".,\"'")
        if not low:
            return raw  # totally empty — invalid
        if low == a.lower() or low.startswith(a.lower()):
            return a
        if low == b.lower() or low.startswith(b.lower()):
            return b
        # Accept shorthand (C/D, S/H).
        if low in {a[0].lower(), a.lower()[:4]}:
            return a
        if low in {b[0].lower(), b.lower()[:4]}:
            return b
        return raw  # invalid — engine will record and skip update
