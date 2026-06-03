# AI Agent Workflow

Macro Regime Kit can be run directly from the CLI. AI agents are optional helpers.

## Install Skill

Codex:

```bash
macro-regime skill-install --target ~/.codex/skills
```

Claude Code:

```bash
macro-regime skill-install --target ~/.claude/skills
```

## First Prompt

```text
Use the macro-regime-monitor skill.
Run macro-regime doctor.
Do not edit my Obsidian vault or credentials.
Explain what is missing and give exact next steps.
```

## Safe Operating Rules

- Let the CLI fetch and score data.
- Ask the agent to verify state freshness.
- Keep thesis feedback in dry-run until reviewed.
- Do not ask the agent to handle trading credentials or wallet private keys.

