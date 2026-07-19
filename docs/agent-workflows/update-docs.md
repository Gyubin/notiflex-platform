# Update Project Documentation

Use this procedure after a completed textbook chapter or when asked to update project documentation.
It is shared by all coding agents. `/update-docs` remains a Claude Code command alias for this file.

1. Identify the chapter's changes from Git history, changed files, installed tools, configuration,
   architecture decisions, and updated operating rules.

2. Update every applicable existing document:
   - `JOURNEY.md`: mark completed subchapters from ⬜ to ✅ with the completion date; record every
     resulting tool decision; query the cluster rather than guessing versions; update node-pool data
     after resource changes.
     - Notiflex image: `kubectl --context notiflex-gke get rollout notiflex-api -n notiflex -o jsonpath='{.spec.template.spec.containers[0].image}'`
     - ArgoCD: `kubectl --context notiflex-gke get deploy argocd-server -n argocd -o jsonpath='{.spec.template.spec.containers[0].image}'`
     - Other tools: `kubectl --context notiflex-gke get pod -n <namespace> -l <label> -o jsonpath='{.items[0].spec.containers[0].image}'`
     - Node pools: `kubectl --context notiflex-gke get nodes -L cloud.google.com/gke-nodepool`
     - When the node pool is paused, query Kubernetes API objects, Helm release metadata, and the
       GKE managed instance group's target size without resuming worker nodes.
   - `AGENTS.md`: update project rules or context when the working contract changed. Keep `CLAUDE.md`
     as the thin compatibility adapter.
   - `docs/architecture-decisions.md`, when it exists: add every new decision from `JOURNEY.md` in
     order, using the next ADR number and a decision statement plus three to four reason bullets.
   - `claude-context/`, when the textbook has introduced it: update the current architecture snapshot
     and its chapter marker. The name is retained for textbook compatibility.
   - `command-guardrails/`, when it exists: update hazardous-operation procedures.

3. Verify the corresponding textbook result template and the documentation diff. When the chapter
workflow requires a documentation commit, commit all resulting documentation using the repository's
Lore commit format, unless the caller explicitly asks not to commit.

Do not create future-chapter artifacts before their textbook guardrail introduces them.
