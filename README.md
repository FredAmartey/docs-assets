# docs-assets

Shared documentation and media assets for public projects.

This repository keeps visual material out of application repositories when it
belongs to historical documentation rather than the product itself. Every
asset lives under a project namespace so multiple repositories can share the
same archive without collisions.

## Layout

```text
projects/<repo>/docs/<area>/
projects/<repo>/pull-requests/<number>-<slug>/
projects/<repo>/releases/<version>/
```

Use lowercase kebab-case for directory and file names. Keep a source and usage
note in each project's README when a batch is imported.

## When to use this repository

Keep an asset in its main project when it is small, current and tightly coupled
to the code or documentation being changed. Put it here when it is historical,
large, shared across projects or needs to outlive a branch or release.

| Asset | Keep in the main project | Put in `docs-assets` |
| --- | --- | --- |
| README images | Current images that change with the README | Historical or shared images |
| Release visuals | Product assets shipped with the release | Release-note screenshots |
| Architecture diagrams | Source diagrams maintained with the code | Exported or cross-project diagrams |
| Demos and media | Small current examples | Larger or historical walkthroughs |
| Benchmarks and QA | Scripts, raw data and reproducible tests | Screenshots and archived evidence |

Each asset should have one canonical owner. Do not duplicate the same file in
both repositories.

## URL policy

Historical references must pin a commit SHA, never `main`:

```text
https://raw.githubusercontent.com/FredAmartey/docs-assets/<commit-sha>/projects/<repo>/pull-requests/<number>-<slug>/image.png
```

Committed paths are immutable. A revised capture gets a new file or a new
directory rather than replacing an existing asset.

## Rights

This repository does not grant a blanket license. Asset rights follow the
source project and any third-party content shown in an image. Check the source
project before reusing an asset outside its documentation context.
