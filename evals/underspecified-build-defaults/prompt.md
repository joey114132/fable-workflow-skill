---
name: underspecified-build-defaults
description: Vague feature request. Does the reply name the few decisions that change the design and commit to defaults, instead of stalling on questions or silently guessing?
tags: [behavior]
expected_outcome: "Names 2+ design-changing decisions, commits to an explicit default for each, and still delivers a concrete build in the same reply."
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Our dental clinic keeps losing money on no-shows, so we want appointment reminders for patients. Build the reminder feature for us. Put the core code in your reply here in the chat, because I'm reading on my phone and can't open files.
