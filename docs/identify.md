---
title: "Identifying a file: identify"
nav_order: 3
---

# Identifying a file: `identify`

```bash
heat3d-battlefield-maps identify <file>
```

says whether a file is a Frostbite table of contents (`.toc`) and what it
holds, by reading it rather than by its name. A Battlefield 6 install has
hundreds of them: `Data\layout.toc`, the installation's list of packages, and
under `Data\Win32\` the superbundle tables, a level's among them.

```text
layout.toc  (<n> bytes)
  Frostbite table of contents, signed
    tree begins at 556
    superbundles <n>
```

The second line says which header the file has (see
[Frostbite](reader-frostbite.md#the-header-that-looks-encrypted-and-is-not));
then either the number of assets its binary sections list, or, for a table
written as a tree, the number of superbundles it names.

## Anything else

A file that is not a Frostbite table prints nothing on the output, the line
`not a Battlefield file` on the error output, and exits with 2. That is what
[3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/)' own
`identify` relies on: for a file its own readers do not know, it asks each
installed game tool in turn, and the one that exits with 0 has the answer.

| Message | Exit | Means |
|---|---|---|
| (the description above) | 0 | a Frostbite table of contents |
| `not a Battlefield file` | 2 | any other file |
| `no such file: <path>` | 2 | the path is wrong |
| `needs 3DHeat GameFiles: ...` | 2 | see [Before you start](before-you-start.md) |
