# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Query pipeline for arachna v4.0.1."""

from pathlib import Path

from .formatter import _generate_header, lang_for_path

_PRE_LABEL_PREFIX = "pre: "


def _collect_import_graph(named_sections, graph_cache):
    cache_key = tuple((fp, hash(content) & 0xFFFFFFFF) for fp, content, _tokens in named_sections)
    if cache_key in graph_cache:
        return graph_cache[cache_key]
    graph = {}
    for filepath, content, _tokens in named_sections:
        deps = _extract_deps_from_content(content)
        if deps is None:
            lang = lang_for_path(Path(filepath))
            header = _generate_header(Path(filepath), content, lang)
            deps = _extract_deps_from_content(header) or []
        graph[filepath] = deps
    if len(graph_cache) > 128:
        graph_cache.clear()
    graph_cache[cache_key] = graph
    return graph


def _extract_deps_from_content(content):
    for line in content.split("\n"):
        if line.startswith("deps: "):
            return [d.strip() for d in line[6:].split(",") if d.strip()]
    return None


def _score_filename(filepath, query_words):
    fname_lower = Path(filepath).name.lower()
    for word in query_words:
        if word in fname_lower:
            return 10
    return 0


def _score_content(filepath, content, query_words):
    content_lower = content.lower()
    score = 0
    for word in query_words:
        if word in content_lower:
            score += 3
    return score


def _score_exports(content, query_words):
    for line in content.split("\n"):
        if line.startswith("exports: "):
            for word in query_words:
                if word in line[9:].lower():
                    return 8
            break
    return 0


def _score_imports(filepath, graph, query_words):
    score = 0
    for dep in graph.get(filepath, []):
        for word in query_words:
            if word in dep.lower():
                score += 5
    return score


def _score_files(named_sections, query_words, graph_cache):
    scores = {}
    graph = _collect_import_graph(named_sections, graph_cache)
    for filepath, content, _tokens in named_sections:
        if filepath.startswith(_PRE_LABEL_PREFIX):
            continue
        score = (
            _score_filename(filepath, query_words)
            + _score_content(filepath, content, query_words)
            + _score_exports(content, query_words)
            + _score_imports(filepath, graph, query_words)
        )
        if score > 0:
            scores[filepath] = score
    return scores


def _build_reverse_graph(graph):
    reverse = {}
    for fpath, deps in graph.items():
        for dep in deps:
            dep_basename = dep.split("/")[-1].split(".")[0]
            reverse.setdefault(dep_basename, []).append(fpath)
            reverse.setdefault(dep, []).append(fpath)
    return reverse


def _expand_import_chain(matched, reverse_graph, depth=2):
    result = set(matched)
    for _ in range(depth):
        new_matches = set()
        for fpath in result:
            basename = Path(fpath).name.split(".")[0]
            for importer in reverse_graph.get(basename, []):
                if importer not in result:
                    new_matches.add(importer)
            for importer in reverse_graph.get(fpath, []):
                if importer not in result:
                    new_matches.add(importer)
        if not new_matches:
            break
        result |= new_matches
    return result


def _build_filtered_sections(named_sections, matched, include_pre_commands):
    result = []
    for section in named_sections:
        if section[0].startswith(_PRE_LABEL_PREFIX):
            if include_pre_commands:
                result.append(section)
        elif section[0] in matched:
            result.append(section)
    return result


def _filter_by_query(named_sections, query, include_pre_commands=False, graph_cache=None):
    if graph_cache is None:
        graph_cache = {}
    if not query or not query.strip():
        return named_sections
    query_words = query.lower().split()
    scores = _score_files(named_sections, query_words, graph_cache)
    if not scores:
        return (
            [s for s in named_sections if s[0].startswith(_PRE_LABEL_PREFIX)]
            if include_pre_commands
            else []
        )
    matched = set(scores.keys())
    graph = _collect_import_graph(named_sections, graph_cache)
    reverse_graph = _build_reverse_graph(graph)
    matched = _expand_import_chain(matched, reverse_graph)
    return _build_filtered_sections(named_sections, matched, include_pre_commands)


def _filter_filenames_by_query(filepaths, query):
    if not query or not query.strip():
        return filepaths
    query_words = query.lower().split()
    result = []
    for fp in filepaths:
        for word in query_words:
            if word in fp.name.lower():
                result.append(fp)
                break
    return result
