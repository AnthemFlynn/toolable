# Test Coverage to 90% - Design

**Date:** 2025-11-30
**Goal:** Increase test coverage from 62% to 90%+ with focus on reliability and security
**Approach:** Critical paths first

## Current State

- **Coverage:** 62% overall (84 tests)
- **Major gaps:**
  - cli.py: 52% (145/303 untested lines)
  - registry.py: 25% (51/68 untested lines)
  - sampling.py: 29% (27/38 untested lines)
  - session.py: 46% (20/37 untested lines)

## Strategy: Three-Phase Approach

### Phase 1: Reliability Core (→75% coverage)

**Goal:** Test paths most likely to fail in production

**A. Timeout Handling Tests (~5 tests)**
- Unix timeout fires correctly (signal.alarm)
- Windows timeout fires correctly (threading.Timer)
- Timeout cleanup in finally block (both platforms)
- Timeout validation (positive, <= 600 seconds)
- Tool completes before timeout doesn't error

**Testing approach:**
- Mock platform.system() for both branches
- Use time.sleep() to trigger actual timeouts
- Monkeypatch signal/threading
- Test cleanup code paths

**B. Registry Subprocess Tests (~8 tests)**
- Successful tool discovery from executable
- Timeout during discovery (5 second limit)
- Malformed JSON response
- Executable doesn't exist
- Non-zero exit code
- Multiple tools in manifest
- Tool with resources and prompts
- Warning emitted on load failure

**Testing approach:**
- Create test executables in tests/fixtures/
- Use real subprocess.run (not mocks)
- Validate warnings.warn() calls
- Test actual JSON parsing

**C. CLI Error Path Tests (~7 tests)**
- Missing arguments for --resource flag
- Missing arguments for --prompt flag
- Unknown command with multiple tools
- Tool returns None
- Tool returns non-JSON-serializable object
- ValidationError with field details
- ToolError during pre_validate()

**Testing approach:**
- Test error messages users see
- Validate error envelope format
- Ensure helpful suggestions provided

**Deliverable:** 20 new tests, 62% → 75% coverage

---

### Phase 2: Security & Correctness (→85% coverage)

**Goal:** Test security-sensitive paths and complex features

**A. Resource URI Security Tests (~6 tests)**
- Literal characters escaped (/files/{id}.json vs /files/123Xjson)
- Anchoring prevents extra paths (/files/{id} vs /files/123/extra)
- Multiple placeholders work correctly
- Special regex chars in pattern
- URI with encoded characters
- Empty/missing placeholder values

**Testing approach:**
- Extend existing test_security_fixes.py
- Test regex patterns with ., *, ?, [, ], (, )
- Verify actual resource function invocation
- Ensure wrong resource never called

**B. Input Validation Edge Cases (~5 tests)**
- Duplicate flags (--name foo --name bar)
- Flag without value at end of args
- JSON parsing in flag values
- Invalid JSON in flag value
- Flag name with dashes (--my-flag → my_flag)

**Testing approach:**
- Test CLI execution with sys.argv monkeypatch
- Document which flag wins (first/last)
- Validate error messages

**C. Sampling Protocol Tests (~4 tests)**
- sample() via stdin request/response roundtrip
- sample() via HTTP POST callback
- stdin closed while waiting
- HTTP timeout or connection error

**Testing approach:**
- Mock stdin with StringIO
- Mock HTTP with unittest.mock
- Test blocking behavior
- Validate request format

**Deliverable:** 15 new tests, 75% → 85% coverage

---

### Phase 3: Completeness (→90% coverage)

**Goal:** Cover remaining paths for polish

**A. CLI Output Tests (~5 tests)**
- --help with no tools
- --help with multiple tools
- Tool --help with parameters
- --tools flag output
- --resources and --prompts flags

**Testing approach:**
- Capture stdout with capsys
- Validate human-readable output
- Test formatting edge cases

**B. Session Protocol Tests (~4 tests)**
- Full session lifecycle
- Session quit mid-flow
- Generator exception during session
- Malformed stdin input

**Testing approach:**
- Mock stdin/stdout for bidirectional I/O
- Test send() protocol
- Validate cleanup

**C. Remaining CLI Paths (~3 tests)**
- Single-tool mode fallback
- --validate with pre_validate errors
- --sample-via configuration

**Deliverable:** 12 new tests, 85% → 90%+ coverage

---

## Implementation Plan

**Total:** ~47 new tests (84 → ~131 tests)
**Time:** 6-9 hours
**Order:** Phase 1 → Phase 2 → Phase 3

**Each phase is independently valuable:**
- Stop after Phase 1: Have reliability confidence (75% coverage)
- Stop after Phase 2: Have security confidence (85% coverage)
- Complete Phase 3: Have full confidence (90%+ coverage)

**Expected bugs found:** 6-12 bugs based on typical untested code

## Success Criteria

- ✅ Coverage >= 90%
- ✅ All timeout scenarios tested (both platforms)
- ✅ All registry subprocess paths tested
- ✅ All error envelopes validated
- ✅ All security-critical code tested
- ✅ No regressions (all existing tests still pass)
