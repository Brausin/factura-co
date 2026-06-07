---
name: test-driven-development
description: Write tests before code. Red-green-refactor cycle.
---

Always write tests first. For every new function:
1. Write a failing test that describes the expected behavior
2. Write the minimum code to make it pass
3. Refactor while keeping tests green

Use pytest. Name tests `test_<function>_<scenario>`. Each test should test ONE behavior.
