---
title: "Identificare un file: identify"
nav_order: 3
lang: "it"
source: identify.md
source_hash: "29c92138c83c"
nav_exclude: true
search_exclude: true
---
# Identificare un file: `identify` {#identifying-a-file-identify}

```bash
heat3d-battlefield-maps identify <file>
```

dice se un file è un indice Frostbite (`.toc`) e che cosa contiene, leggendolo invece di guardarne
il nome. Un'installazione di Battlefield 6 ne ha centinaia: `Data\layout.toc`, l'elenco dei pacchetti
dell'installazione, e in `Data\Win32\` le tabelle dei superbundle, tra cui quella di un livello.

```text
layout.toc  (<n> bytes)
  Frostbite table of contents, signed
    tree begins at 556
    superbundles <n>
```

La seconda riga dice quale intestazione ha il file (vedi
[Frostbite](reader-frostbite.md#the-header-that-looks-encrypted-and-is-not));
poi, il numero di asset che le sue sezioni binarie elencano, oppure, per una tabella scritta come albero,
il numero di superbundle che nomina.

## Qualsiasi altro file {#anything-else}

Un file che non è una tabella Frostbite non stampa nulla sull'uscita, la riga
`not a Battlefield file` sull'uscita degli errori, e termina con 2. È ciò su cui si basa lo
strumento `identify` di [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/):
per un file che i suoi lettori non conoscono, chiede a ogni strumento di gioco installato a turno,
e quello che termina con 0 ha la risposta.

| Messaggio | Uscita | Significa |
|---|---|---|
| (la descrizione sopra) | 0 | un indice Frostbite |
| `not a Battlefield file` | 2 | qualsiasi altro file |
| `no such file: <path>` | 2 | il percorso è sbagliato |
| `needs 3DHeat GameFiles: ...` | 2 | vedi [Prima di iniziare](before-you-start.md) |
