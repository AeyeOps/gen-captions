python_sources(dependencies=[":project-version"])

resource(name="project-version", source="VERSION")

pex_binary(
    name="gen-captions",
    entry_point="gen_captions.cli",
)
