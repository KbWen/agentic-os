#!/usr/bin/env python3
"""Schema gate-safety validator for downstream-capabilities.yaml (ADR-007 AC-D6).

Makes gate-relaxation UNREPRESENTABLE: a present capabilities file is REJECTED
(exit 1, naming the offending field) - never silently clamped - if it registers a
non-`custom-*` skill, raises a skill above the `on-match` load_policy ceiling, or
declares anything that could relax/escalate a gate (gate / ship-edge / block_if_missed
/ trigger_priority / concurrent-writer / blocking tracker).

  exit 0 = gate-safe (or absent / empty -> inert)
  exit 1 = NOT gate-safe (a forbidden/over-cap field, reason on stderr)
  exit 2 = MALFORMED / unsupported syntax -> fail-closed

The file is parsed by a dedicated STRICT, dependency-free mini-parser (`parse_strict`),
NOT the lenient shared `_yaml_loader`. The capabilities schema needs only a tiny block
subset (block mappings/sequences, plain or simple-quoted scalars, and `[a, b]` flow
sequences of plain scalars); `parse_strict` accepts ONLY that and RAISES on EVERYTHING
else - flow mappings `{}`, anchors `&`, aliases `*`, tags `!`, merge keys `<<`, explicit
keys `?`, backslash escapes, block scalars `>`/`|`, inline comments, tabs, multi-doc
markers, and ANY misaligned indentation. This flips the security argument from a denylist
of dangerous syntax (whack-a-mole, the source of repeated fail-opens) to an ALLOWLIST of
permitted syntax: any construct that could make the parser's resolved keys diverge from a
spec parser is a hard syntax error, so a forbidden key cannot hide behind parser leniency.
The shared `_yaml_loader` (which legitimately serves trigger-registry.yaml, where tokens
like `trigger_priority` are valid data) is intentionally NOT used or modified here -> zero
blast radius on its ~20 other consumers.
"""
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Strict capabilities-grammar parser (dependency-free, fail-closed by default)
# ---------------------------------------------------------------------------

class _StrictError(ValueError):
    """Raised on any syntax outside the minimal capabilities grammar (fail-closed)."""


def _coerce(scalar):
    if scalar in ("true", "false"):
        return scalar == "true"
    if scalar in ("null", "~"):
        return None
    try:
        return int(scalar)
    except ValueError:
        return scalar


# characters that introduce YAML features the strict grammar refuses to interpret
_DISALLOWED = ("{", "}", "&", "*", "!", "\\", "#", "<", ">", "|", "?")


def _strict_quoted(tok, lineno):
    q = tok[0]
    if len(tok) < 2 or tok[-1] != q:
        raise _StrictError("unterminated/mismatched quote (line %d): %r" % (lineno, tok))
    inner = tok[1:-1]
    if "\\" in inner or q in inner:
        raise _StrictError("escapes / embedded quotes not allowed (line %d): %r" % (lineno, tok))
    return inner


def _strict_plain(tok, lineno):
    if not tok:
        raise _StrictError("empty scalar (line %d)" % lineno)
    if any(c in tok for c in _DISALLOWED) or "[" in tok or "]" in tok or ":" in tok:
        raise _StrictError("unsupported plain scalar (line %d): %r" % (lineno, tok))
    return _coerce(tok)


def _strict_atom(tok, lineno):
    """A flow-sequence element or a simple scalar: plain or simple-quoted only."""
    tok = tok.strip()
    if tok[:1] in ("'", '"'):
        return _strict_quoted(tok, lineno)
    return _strict_plain(tok, lineno)


def _strict_value(tok, lineno):
    tok = tok.strip()
    if tok in (">", "|"):
        raise _StrictError("block scalars not allowed (line %d)" % lineno)
    if tok[:1] in ("'", '"'):
        return _strict_quoted(tok, lineno)
    if tok[:1] == "[":
        if not tok.endswith("]"):
            raise _StrictError("malformed flow sequence (line %d): %r" % (lineno, tok))
        inner = tok[1:-1].strip()
        if not inner:
            return []
        return [_strict_atom(p, lineno) for p in inner.split(",")]
    return _strict_plain(tok, lineno)


def _strict_key(tok, lineno):
    tok = tok.strip()
    if tok[:1] in ("'", '"'):
        return _strict_quoted(tok, lineno)
    if tok == "<<":
        raise _StrictError("merge keys not allowed (line %d)" % lineno)
    if any(c in tok for c in _DISALLOWED) or "[" in tok or "]" in tok or ":" in tok or "," in tok:
        raise _StrictError("unsupported key (line %d): %r" % (lineno, tok))
    return tok


def _colon_index(s):
    """Index of the key/value-separating ':' (followed by space or EOL), ignoring
    colons inside quotes. -1 if none."""
    q = None
    for i, c in enumerate(s):
        if q is not None:
            if c == q:
                q = None
        elif c in ("'", '"'):
            q = c
        elif c == ":" and (i + 1 >= len(s) or s[i + 1] == " "):
            return i
    return -1


def parse_strict(text):
    """Parse the minimal capabilities grammar. Raise _StrictError on anything else."""
    toks = []  # (indent, content, lineno)
    for lineno, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise _StrictError("tab character not allowed (line %d)" % lineno)
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s in ("---", "..."):
            raise _StrictError("document markers / multi-doc not allowed (line %d)" % lineno)
        indent = len(raw) - len(raw.lstrip(" "))
        toks.append((indent, s, lineno))
    if not toks:
        return {}
    idx = [0]
    result = _parse_block(toks, idx, toks[0][0])
    if idx[0] != len(toks):
        raise _StrictError("misaligned indentation (line %d)" % toks[idx[0]][2])
    return result


def _parse_block(toks, idx, base):
    return _parse_seq(toks, idx, base) if toks[idx[0]][1].startswith("- ") else _parse_map(toks, idx, base)


def _parse_map(toks, idx, base):
    out = {}
    while idx[0] < len(toks):
        ind, s, lineno = toks[idx[0]]
        if ind < base:
            break
        if ind > base:
            raise _StrictError("misaligned indentation (line %d)" % lineno)
        if s.startswith("- "):
            raise _StrictError("sequence item in mapping context (line %d)" % lineno)
        ci = _colon_index(s)
        if ci < 0:
            raise _StrictError("expected 'key: value' (line %d): %r" % (lineno, s))
        key = _strict_key(s[:ci], lineno)
        if key in out:
            raise _StrictError("duplicate key %r (line %d)" % (key, lineno))
        rest = s[ci + 1:].strip()
        idx[0] += 1
        if rest == "":
            if idx[0] < len(toks) and toks[idx[0]][0] > base:
                out[key] = _parse_block(toks, idx, toks[idx[0]][0])
            else:
                out[key] = {}
        else:
            out[key] = _strict_value(rest, lineno)
    return out


def _parse_seq(toks, idx, base):
    out = []
    while idx[0] < len(toks):
        ind, s, lineno = toks[idx[0]]
        if ind < base:
            break
        if ind > base:
            raise _StrictError("misaligned indentation (line %d)" % lineno)
        if not s.startswith("- "):
            raise _StrictError("expected '- item' (line %d): %r" % (lineno, s))
        content = s[2:].strip()
        item_indent = base + 2
        sub = [(item_indent, content, lineno)]
        idx[0] += 1
        while idx[0] < len(toks) and toks[idx[0]][0] > base:
            ti, ts, tl = toks[idx[0]]
            if ti < item_indent:
                raise _StrictError("misaligned indentation (line %d)" % tl)
            sub.append((ti, ts, tl))
            idx[0] += 1
        if _colon_index(content) >= 0 or len(sub) > 1:
            si = [0]
            item = _parse_map(sub, si, item_indent)
            if si[0] != len(sub):
                raise _StrictError("misaligned indentation (line %d)" % sub[si[0]][2])
            out.append(item)
        else:
            out.append(_strict_value(content, lineno))
    return out


# ---------------------------------------------------------------------------
# Schema gate-safety checks (run on the strictly-parsed structure)
# ---------------------------------------------------------------------------

ALLOWED_LOAD_POLICY = {"on-match"}
ALLOWED_SUBAGENT_POLICY = {"read-only", "governed"}
# keys that could relax / escalate a gate anywhere in the doc -> hard reject (fail-closed)
FORBIDDEN_KEYS = {"gate", "gates", "ship_edge", "ship_edges", "block_if_missed",
                  "trigger_priority", "worklog_writers", "blocking", "hard"}
# knowledge_sources (ADR-009): a present-only, advisory-ONLY KB consumption pointer.
# A KB can inform an agent but can NEVER gate/relax a phase: role is fixed to advisory,
# the key-allowlist rejects required/gate/etc., and manifest_trusted defaults false.
ALLOWED_KS_KEYS = {"id", "path", "entrypoint", "role", "manifest_trusted", "tier_source", "description"}
ALLOWED_KS_ROLE = {"advisory"}


def _forbidden(obj, where="root"):
    if isinstance(obj, dict):
        for key, val in obj.items():
            if str(key).strip().lower() in FORBIDDEN_KEYS:
                return "%s.%s" % (where, key)
            hit = _forbidden(val, "%s.%s" % (where, key))
            if hit:
                return hit
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            hit = _forbidden(val, "%s[%d]" % (where, i))
            if hit:
                return hit
    return None


def validate(data):
    """Return None if gate-safe, else a 1-line reason naming the offending field."""
    if data is None or data == {}:
        return None  # empty / absent = inert = safe (present-only)
    if not isinstance(data, dict):
        return "top-level must be a mapping"
    hit = _forbidden(data)
    if hit:
        return "forbidden gate-relaxing key: %s" % hit
    # ALLOWLIST (not just a denylist): an unknown top-level key cannot be smuggled in
    # as a future escalation surface -> gate-relaxation is structurally unrepresentable.
    for key in data:
        if str(key) not in {"version", "skills", "subagent_policy", "trackers", "knowledge_sources"}:
            return ("unknown top-level key %r - only version/skills/subagent_policy/trackers/"
                    "knowledge_sources are allowed (gate-relaxation is unrepresentable)" % key)
    for i, sk in enumerate(data.get("skills") or []):
        if not isinstance(sk, dict):
            return "skills[%d] must be a mapping" % i
        sid = str(sk.get("id", ""))
        if not sid.startswith("custom-"):
            return "skills[%d].id %r is not custom-* (downstream skills MUST be custom-*)" % (i, sid)
        lp = sk.get("load_policy", "on-match")
        if lp not in ALLOWED_LOAD_POLICY:
            return "skills[%d].load_policy %r must be on-match (the downstream capability ceiling)" % (i, lp)
        ps = sk.get("phase_scope")
        if ps is not None and not isinstance(ps, list):
            return "skills[%d].phase_scope must be a list" % i
        for sk_key in sk:
            if str(sk_key) not in {"id", "load_policy", "phase_scope", "detect_by", "cost_risk", "description"}:
                return "skills[%d] unknown key %r (allowlist: id/load_policy/phase_scope/detect_by/cost_risk/description)" % (i, sk_key)
    sp = data.get("subagent_policy", "read-only")
    if sp not in ALLOWED_SUBAGENT_POLICY:
        return "subagent_policy %r invalid (allowed: read-only | governed)" % sp
    for i, tr in enumerate(data.get("trackers") or []):
        if not isinstance(tr, dict):
            return "trackers[%d] must be a mapping" % i
    for i, ks in enumerate(data.get("knowledge_sources") or []):
        if not isinstance(ks, dict):
            return "knowledge_sources[%d] must be a mapping" % i
        if not str(ks.get("path", "")).strip():
            return "knowledge_sources[%d] requires a non-empty path" % i
        role = ks.get("role", "advisory")
        if not isinstance(role, str) or role not in ALLOWED_KS_ROLE:
            return ("knowledge_sources[%d].role %r must be advisory "
                    "(a knowledge source can never be authority / gate a phase)" % (i, role))
        mt = ks.get("manifest_trusted", False)
        if not isinstance(mt, bool):
            return "knowledge_sources[%d].manifest_trusted must be true/false (default false)" % i
        for ks_key in ks:
            if str(ks_key) not in ALLOWED_KS_KEYS:
                return ("knowledge_sources[%d] unknown key %r (allowlist: "
                        "id/path/entrypoint/role/manifest_trusted/tier_source/description)" % (i, ks_key))
    return None


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: validate_downstream_capabilities.py <file>\n")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        return 0  # absent = inert = safe (present-only)
    try:
        data = parse_strict(path.read_text(encoding="utf-8"))
    except _StrictError as exc:
        # Unsupported syntax in a capabilities file -> cannot be safely interpreted.
        # Fail closed (exit 2) rather than risk a parser-divergence gate-relaxation.
        sys.stderr.write("MALFORMED: downstream-capabilities.yaml uses unsupported syntax - %s\n" % exc)
        return 2
    except Exception as exc:  # pragma: no cover - defensive
        sys.stderr.write("MALFORMED: cannot parse %s (%s)\n" % (path, exc))
        return 2
    reason = validate(data)
    if reason is None:
        sys.stdout.write("OK: downstream-capabilities.yaml is gate-safe\n")
        return 0
    sys.stderr.write("FAIL: downstream-capabilities.yaml is NOT gate-safe - %s\n" % reason)
    return 1


if __name__ == "__main__":
    sys.exit(main())
