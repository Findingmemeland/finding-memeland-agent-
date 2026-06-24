# Finding Memeland — Agent

Autonomous AI agent that runs the Finding Memeland treasure-hunt game on Base.
See the litepaper (v0.3) and the launch checklist (v1.1) for the full design.

> **Status:** scaffold. Modules are stubbed with the validated game logic in
> place (templates, integrity hash, validation order, state machine). On-chain
> and X-API calls are interface stubs marked `# TODO`. This is the deliverable
> of checklist **step 21**; the working implementation is steps 23–28.

## What this agent does

Each *hunt* is a self-contained game:

1. **Persona Dresser** picks a warmed-up account from the pipeline and dresses it
   with an AI-generated identity (display name, bio, avatar). The `@` handle
   never changes (X API can't change handles).
2. **Clue Engine** publishes Clue 1 on the main `@FindingMemeland` account. Clue 1
   = hunt announcement + reshare gate + the **integrity hash**. Further clues drop
   at random 1–3h intervals, ~30% more obvious each time, no cap.
3. **DM Listener + Validator** polls DMs on the main account. First DM with the
   correct claim code + a wallet that passes holding, reshare and bot checks wins.
4. **Payout Engine** sends the prize in $FMML from the hot wallet.
5. After a 1h reveal window, the persona is permanently retired.

Game posts publish **autonomously** — no human approval. Only non-game posts
(pinned rules, filler/teaser) go through the Telegram approval queue. The
operator never sees a clue before it publishes (operational blindness).

## Architecture

```
src/finding_memeland/
├── config.py              # env-driven settings (Doppler-backed)
├── main.py                # entrypoint: boots orchestrator + listeners
├── db/client.py           # Supabase client + repositories
├── persona/
│   ├── generator.py       # LLM identity generation
│   └── dresser.py         # apply identity to a pool account / retire it
├── content/
│   ├── clue_engine.py     # clue trajectory + easing curve
│   ├── integrity.py       # SHA-256 commitment hash
│   ├── templates.py       # validated post templates (frozen)
│   └── guardrails.py      # pre-publish safety checks
├── orchestrator/
│   └── state_machine.py   # LangGraph hunt lifecycle
├── dm/
│   ├── listener.py        # poll main-account DMs
│   └── validator.py       # 4-filter eligibility check
├── chain/
│   ├── holdings.py        # continuous-balance check via Base RPC
│   └── payout.py          # prize transfer from hot wallet
├── social/x_client.py     # X API wrapper (one app, many OAuth'd personas)
├── telegram/approval_queue.py  # approval for non-game posts only
└── supervisor/watchdog.py # anomaly detection + kill switch
```

## Hunt state machine

```
idle → preparing → live → resolving → paying → pending_cleanup (1h) → retiring → idle
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# secrets via Doppler (see doppler.md); never commit a .env
doppler run -- PYTHONPATH=src python -m finding_memeland.main
```

1. Create the Supabase project and run `db/schema.sql`.
2. Create the Doppler project and set every variable in `doppler.md`.
3. Warm each persona (~10 days), then authorize it:
   `python scripts/authorize_persona.py <ref>` (step 16) — stores its tokens and
   registers it as `ready`.

## Boot & run a hunt

`main.build_agent()` is the composition root: it builds the Anthropic, OpenAI,
web3, Supabase and X clients and wires them, through the runtime adapters, into
the `Orchestrator`. `main()` then starts the Telegram admin loop.

The agent boots idle. The admin fires a hunt with **/launch** from the hardcoded
admin chat; the hunt runs in a background thread. A hunt only runs once
`FMML_TOKEN_ADDRESS`, `FMML_USD_PRICE`, `HOT_WALLET_PRIVATE_KEY`,
`PAYOUT_CAP_FMML` and `INTEGRITY_SALT` are set (`assert_ready_for_hunt`).

## Validation scripts (run as you go)

- `scripts/spike_dm_read.py` / `spike_x_v2.py` — confirm X reads/writes in your tier
- `scripts/generate_persona_sample.py` / `generate_clues_sample.py` — eyeball content
- `scripts/generate_avatar_sample.py` — persona + avatar end-to-end
- `scripts/simulate_hunt.py` — full hunt dry-run (real content, fake X/chain)
- `scripts/test_payout.py` — on-chain payout on Base Sepolia
- `scripts/test_supabase.py` — DB round-trip
- `scripts/check_findability.py` — pre-hunt: is the persona locatable?

## Deploy (Railway)

The `Procfile` runs the worker. On Railway: create a project from this repo,
enable the **Doppler ↔ Railway** integration (config `prd`) so secrets are
injected, and deploy. No `doppler` CLI needed in prod — Railway injects env.

## Cost note

The X API is pay-per-use. Reads are billed per result returned; polling an empty
inbox is free. Validate in cost order — claim code (free) → holding (free) →
reshare (paid). Never put URLs in clues ($0.20 each). Budget ~$15–30/hunt.

## Security

- No secret ever lives in this repo. All credentials come from Doppler at runtime.
- The agent's hot wallet holds at most 1–2 hunts' worth of prizes, with a
  hardcoded per-hunt cap. The treasury Safe is separate and the agent has no
  access to it.
