---
title: "Eine Datei erkennen: identify"
nav_order: 3
lang: "de"
source: identify.md
source_hash: "29c92138c83c"
nav_exclude: true
search_exclude: true
---
# Eine Datei erkennen: `identify` {#identifying-a-file-identify}

```bash
heat3d-battlefield-maps identify <file>
```

sagt, ob eine Datei eine Frostbite-Inhaltstabelle (`.toc`) ist und was sie enthält, indem
sie die Datei liest und nicht nach dem Namen geht. Eine Battlefield-6-Installation hat
Hunderte davon: `Data\layout.toc`, die Paketliste der Installation, und unter
`Data\Win32\` die Superbundle-Tabellen, darunter die eines Levels.

```text
layout.toc  (<n> bytes)
  Frostbite table of contents, signed
    tree begins at 556
    superbundles <n>
```

Die zweite Zeile sagt, welchen Header die Datei hat (siehe
[Frostbite](reader-frostbite.md#the-header-that-looks-encrypted-and-is-not)); danach folgt
entweder die Anzahl der Assets, die ihre Binärabschnitte auflisten, oder, bei einer als
Baum geschriebenen Tabelle, die Anzahl der Superbundles, die sie nennt.

## Alles andere {#anything-else}

Eine Datei, die keine Frostbite-Tabelle ist, gibt auf der Ausgabe nichts aus, auf der
Fehlerausgabe die Zeile `not a Battlefield file` und endet mit 2. Darauf verlässt sich das
eigene `identify` von [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/): Bei
einer Datei, die seine eigenen Leser nicht kennen, fragt es jedes installierte Spiel-Werkzeug
der Reihe nach, und das, das mit 0 endet, hat die Antwort.

| Meldung | Exit | Bedeutung |
|---|---|---|
| (die Beschreibung oben) | 0 | eine Frostbite-Inhaltstabelle |
| `not a Battlefield file` | 2 | jede andere Datei |
| `no such file: <path>` | 2 | der Pfad ist falsch |
| `needs 3DHeat GameFiles: ...` | 2 | siehe [Bevor du anfängst](before-you-start.md) |
