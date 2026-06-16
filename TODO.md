# TODO

## v4.1.1 — Remote profile selection + SonarCloud cleanup
- [ ] remote: true profile field — explicit marker for remote collection profiles
- [ ] Strict --profile: exact match or error (no silent fallback)
- [ ] Auto-selection: one remote profile → use it, multiple → error with names, none → auto-detect
- [ ] ValueError with available profile names when ambiguous or missing
- [ ] is_excluded: support ** glob patterns — fnmatch limitation requires * prefix workaround
- [ ] SonarCloud: mark 12 vulnerabilities as false positives (S2083 path from config, S5443 tmp in tests, S8565 no deps, S5145 logging, S2612 chmod in tests)

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
