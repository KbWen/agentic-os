# Testing Protocol v3.2

> **This document guides the AI Agent to produce high-quality, trustworthy, and defensive test code.**

## 1. Naming Convention

Test function names should be descriptive and "self-documenting."

- **Format**: `test_[behavior]_[expected_result]_[scenario]`
- **Example**: `test_calculate_total_should_precision_round_when_multiple_items_exist`
- **Anti-pattern**: `test_calculation1` (Never use meaningless numbers)

---

## 2. Coverage Priorities

### 2.1 Happy Path

- Verify basic expected output when input is valid.

### 2.2 Boundary & Edge Cases

- **Numeric**: `0`, negative numbers, max values, `null`, `undefined`.
- **Collections**: Empty arrays, duplicate elements, excessively long strings.
- **Timing**: Synchronous vs. Asynchronous latencies.

### 2.3 Error Handling

- Verify that the system "Throws Errors" or returns specific error codes correctly when encountering invalid input, rather than crashing.

---

## 3. Safety & Independence

- **Isolation**: Tests should not depend on external databases or network APIs (prioritize Mocks/Stubs).
- **Side Effects**: Clean up all temporary state or files after execution; do not leave a persistent impact on the environment.
- **Determinism**: Do not use non-deterministic variables (e.g., current time); inject a Mock clock instead.

---

## 4. Quick Command Example

When you need the AI to reinforce tests:
> "*Read .agentcortex/docs/TESTING_PROTOCOL.md and complete test coverage for [function_name] according to the specifications.*"

---

## 5. Acceptance Criteria (AC)

- All test cases must pass under `npm test` (or the project's corresponding command).
- No "empty tests" (tests without assertions) just to increase coverage.
