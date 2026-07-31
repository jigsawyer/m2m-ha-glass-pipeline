Title: Enterprise GitOps, CI/CD Pipeline, and Agent Isolation
Date: 2026-07-31
Status: Accepted

# 0037. Enterprise GitOps, CI/CD Pipeline, and Agent Isolation

## Context

AI Agents are nondeterministic. Allowing them to trigger deployments locally or via state files (`agent_status.json`) creates a Split-Brain problem between the local environment, Git, and the Edge server.

## Decision

We are adopting strict GitOps. Agents are completely stripped of deployment capabilities. Local deployment scripts (e.g., `publish_edge.sh`) are off-limits to agents. The handoff mechanism is exclusively via Git. Agents will generate code, validate locally using `build_engine.py`, and push to a remote branch. A deterministic CI/CD orchestrator will handle testing and deployment.

## Consequences

Complete Separation of Concerns. Git becomes the single source of truth. Zero risk of local desync.
