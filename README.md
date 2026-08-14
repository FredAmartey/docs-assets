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
