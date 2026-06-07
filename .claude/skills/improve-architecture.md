---
name: improve-codebase-architecture
description: Refactor toward clean, modular, testable code.
---

When improving code architecture:
- Each module should have one clear responsibility
- Functions should be pure where possible (no side effects)
- Dependencies flow inward (business logic doesn't know about I/O)
- Make the common case easy, the rare case possible
- If a file is longer than 200 lines, consider splitting it
