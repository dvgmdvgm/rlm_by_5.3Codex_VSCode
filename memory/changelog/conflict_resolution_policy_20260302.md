# Conflict Resolution Policy — 2026-03-02

## META
- id: conflict_resolution_policy_20260302
- updated_at: 2026-03-02T02:05:00Z
- source: user request

### Winner Selection Order
- status: `active` beats `deprecated`
- priority: higher integer wins
- timestamp: newer `ts` wins
- source rank: `session:*` > `memory/changelog/*` > `memory/*`

### Behavior
- Rules sharing the same `conflict_key` are considered conflicting.
- Only the winning active rule is published to canonical memory.
- Losers are marked deprecated and excluded from canonical output.
