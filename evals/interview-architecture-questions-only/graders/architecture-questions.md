---
type: llm
---
The user asked to be interviewed about a notification system (email, push, in-app) before anything is built, and already stated: solo backend dev, about 2k users now and 50k in a year, a single Django monolith on one VM with Postgres. Judge the assistant's final reply only.

An "architecture-changing question" is one whose answer would change the core design: for example delivery guarantees (can a notification be lost, sent twice, or arrive late), what triggers notifications (domain events vs scheduled vs user-initiated) and expected burst volume, the user preference and opt-out model, whether in-app needs real-time delivery, ordering or batching and digest needs, build-versus-buy for providers, or compliance constraints. Trivia is a question about naming, library flavor, UI styling, code style, or anything that would not change the design.

PASS only if ALL hold:
1. The reply is an interview: it asks questions and does not go on to build the system or present a full design or code.
2. It asks between 1 and 8 questions in total (a numbered item with several sub-questions counts each one).
3. At least 2 of its questions are architecture-changing, and trivia is at most 1 question.
4. It does not re-ask anything the user already stated (number of users, growth, backend stack, database, deployment, team size).

FAIL if ANY hold:
- It builds or delivers a design or code instead of interviewing.
- It asks more than 8 questions in total.
- Most of its questions are trivia.
- It re-asks something the user stated in the message.
