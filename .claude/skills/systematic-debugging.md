---
name: systematic-debugging
description: Debug methodically, not by intuition.
---

When something fails:
1. Read the full error message before doing anything
2. Reproduce the error with the minimal possible input
3. Form a hypothesis about the cause
4. Test the hypothesis — don't just try random fixes
5. Fix the root cause, not the symptom
6. Add a test that would catch this regression
