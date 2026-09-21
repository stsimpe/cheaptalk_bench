"""Rebuild every prompt each agent was shown in a finished run, and check it.

The records do not store prompts, so this replays the code path the engine
used (Agent._system_prompt, build_ct_* and format_history) over the recorded
history, for every agent, round and phase, and checks what the agent saw:

  - the network paragraph and neighbour count match the recorded topology,
    and no star wording reaches a non-star agent (the 2026-09-20 bug);
  - with the corrected prompt, the routing sentence is the topology's own;
    a no_comm prompt carries no messaging paragraph;
  - the context-framing paragraph is present exactly when configured;
  - the horizon stays hidden (no total-rounds wording in the prompt);
  - the history window is the last 10 rounds, the agent's own row is its own
    action and payoff, and only neighbours' actions are shown;
  - the messages an agent receives are exactly its neighbours' messages.

Run it on every new batch:

    python verify_prompts.py <run folder> [<run folder> ...]

Hits of "horizon" wording can come from the models' OWN messages (an agent at
"Current round: 16" writing "sixteen rounds"); those are listed, check them.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import ExperimentConfig, ModelConfig
from engine import make_engine
from message_policies import CONTEXT_FRAMING_PARAGRAPHS, get_extra_message_instruction
from prompts import build_no_comm_user, build_ct_communicate_user, build_ct_action_user

STAR_WORDS = re.compile(r'central agent|peripheral|star network|hub', re.I)
HORIZON = re.compile(r'\b16 rounds|\bof 16\b|sixteen|total (number of )?rounds|final round|rounds remain|remaining rounds', re.I)


def intkeys(d):
    return {int(k): (intkeys(v) if isinstance(v, dict) else v) for k, v in d.items()}


def load(p):
    r = json.load(open(p, encoding='utf-8'))
    c = dict(r['config'])
    c['model'] = ModelConfig(**c['model'])
    c = {k: v for k, v in c.items() if k in ExperimentConfig.__dataclass_fields__}
    cfg = ExperimentConfig(**c)
    hist = []
    for x in r['history']:
        y = dict(x)
        for k in ('actions', 'payoffs', 'messages', 'messages_seen_by', 'invalid', 'reasonings'):
            if k in y and isinstance(y[k], dict):
                y[k] = intkeys(y[k])
        hist.append(y)
    return r, cfg, hist


def check(p, show=None):
    r, cfg, hist = load(p)
    eng = make_engine(cfg)
    agents = eng.build_agents(client=None, run_id=r['run_id'])
    topo = eng.topology
    errs = []
    n_prompts = 0
    for rnd in range(1, len(hist) + 1):
        past = hist[:rnd - 1]
        rec = hist[rnd - 1]
        for a in agents:
            i = a.agent_id
            nbs = topo.neighbors(i)
            sysp = a._system_prompt()
            htxt = a._history_text(past)
            prompts = {'system': sysp}
            if cfg.condition == 'no_comm':
                prompts['action'] = build_no_comm_user(htxt, rnd)
            else:
                extra = get_extra_message_instruction(cfg.message_policy, cfg.framing_type)
                prompts['message'] = build_ct_communicate_user(htxt, rnd, extra_instruction=extra)
                own = rec.get('messages_composed', rec['messages'])[i] if 'messages_composed' in rec else rec['messages'][i]
                prompts['action'] = build_ct_action_user(htxt, rnd, own, rec['messages_seen_by'][i])
            n_prompts += len(prompts)
            full = '\n'.join(prompts.values())
            # --- network description
            if topo.name != 'star' and STAR_WORDS.search(full):
                errs.append(f'r{rnd} a{i}: star wording')
            if f'You have {len(nbs)} neighbor' not in sysp:
                errs.append(f'r{rnd} a{i}: wrong neighbour count in prompt')
            if cfg.condition == 'cheap_talk':
                want = topo.describe_communication(i) if cfg.topology_aware_comm_prompt else None
                if want and want not in sysp:
                    errs.append(f'r{rnd} a{i}: routing sentence missing')
            elif 'Messages travel' in sysp:
                errs.append(f'r{rnd} a{i}: no_comm prompt mentions messages')
            # --- framing
            ctx = CONTEXT_FRAMING_PARAGRAPHS.get(cfg.context_framing, '')
            if ctx and ctx not in sysp:
                errs.append(f'r{rnd} a{i}: context framing missing')
            if not ctx and 'Context:' in sysp:
                errs.append(f'r{rnd} a{i}: stray context framing')
            # --- hidden horizon
            if HORIZON.search(full):
                errs.append(f'r{rnd} a{i}: horizon leak: {HORIZON.search(full).group(0)!r}')
            # --- history: window, own row, neighbours only
            shown = re.findall(r'--- Round (\d+) ---', htxt)
            want_rounds = [str(k) for k in range(max(1, rnd - 10), rnd)]
            if shown != want_rounds:
                errs.append(f'r{rnd} a{i}: history rounds {shown} != {want_rounds}')
            seen_ids = sorted(set(int(x) for x in re.findall(r'Neighbor #(\d+) chose', htxt)))
            if past and seen_ids != sorted(nbs):
                errs.append(f'r{rnd} a{i}: history shows actions of {seen_ids}, neighbours {nbs}')
            for h in past[-10:]:
                if f"You chose: {h['actions'][i]}  (payoff this round: {h['payoffs'][i]})" not in htxt:
                    errs.append(f'r{rnd} a{i}: own row wrong for round {h["round"]}'); break
            # --- messages: exactly what the neighbours sent, nothing else
            if cfg.condition == 'cheap_talk':
                recv = re.findall(r'From neighbor #(\d+): "(.*)"', prompts['action'].split('### Current round')[1])
                want = sorted((str(s), rec['messages'][s]) for s in nbs)
                if sorted(recv) != want:
                    errs.append(f'r{rnd} a{i}: received {recv} != {want}')
                senders_in_hist = set(int(x) for x in re.findall(r'From neighbor #(\d+)', htxt))
                if not senders_in_hist <= set(nbs):
                    errs.append(f'r{rnd} a{i}: history shows messages from non-neighbours {senders_in_hist}')
            if show and (rnd, i) == show:
                for k, v in prompts.items():
                    print(f'\n######## {k.upper()} (round {rnd}, agent {i}) ########\n{v}')
    return n_prompts, errs


if __name__ == '__main__':
    roots = sys.argv[1:]
    total = 0; bad = 0; files = 0
    for root in roots:
        for p in sorted(glob.glob(f'{root}/*/*/*.json')):
            n, errs = check(p)
            total += n; files += 1
            if errs:
                bad += 1
                print(p, errs[:3])
    print(f'\n{files} runs, {total} prompts rebuilt, runs with a problem: {bad}')
