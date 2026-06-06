# TODO

## v2.2.0 — Language presets expansion
- [ ] Add Go preset: go.json (main.go, go.mod, go.sum, *.go)
- [ ] Add Rust preset: rust.json (Cargo.toml, src/*.rs, *.rs)
- [ ] Add Zig preset: zig.json (build.zig, src/*.zig, *.zig)
- [ ] Add Lua preset: lua.json (*.lua, *.rockspec)
- [ ] Add Elixir preset: elixir.json (mix.exs, lib/*.ex, *.exs)
- [ ] Add Haskell preset: haskell.json (*.cabal, stack.yaml, src/*.hs)
- [ ] Add Gleam preset: gleam.json (gleam.toml, src/*.gleam)
- [ ] Update formatter.py _EXT_LANG with new extensions
- [ ] Lazy loading for presets via @functools.lru_cache
- [ ] Tests: detect + preset_to_profile for each new language

## v2.3.0 — Watch improvements
- [ ] Structural diff for pre_commands output (not raw text)
- [ ] --snapshot diff command: diff two snapshots without current files
- [ ] Snapshot tags/labels for grouping (e.g. "release", "audit")

## Backlog
- [ ] Plugin system for custom formatters and tokenizers (v3.0)

