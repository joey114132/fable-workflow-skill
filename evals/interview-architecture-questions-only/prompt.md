---
name: interview-architecture-questions-only
description: Explicit "interview me" request. Are the questions few, ones that change the architecture, and not already answered by the context given?
tags: [behavior]
expected_outcome: "A short set of architecture-changing questions, no build yet, nothing already stated in the prompt re-asked."
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
I want to add a notification system to our SaaS app: email, push, and probably in-app. Before you build anything, interview me about it. Some context: I'm the only backend dev, we have about 2k users now and expect around 50k within a year, and it's a single Django monolith on one VM with Postgres.
