def patch_size_caveat_note(
    *,
    marker: str,
    path_phrase: str = "those paths",
) -> str:
    return (
        f"Patch size metrics marked with {marker} have setup-created "
        "untracked path caveats; changed-file counts/lists and boundary "
        "metrics include detected caveat paths, but line-count metrics "
        f"may not fully represent {path_phrase}."
    )
