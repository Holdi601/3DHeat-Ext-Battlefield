---
title: "Bevor du anfängst"
nav_order: 1.5
lang: "de"
source: before-you-start.md
source_hash: "f55c65c6279e"
nav_exclude: true
search_exclude: true
---
# Bevor du anfängst {#before-you-start}

Neu auf der Kommandozeile? Diese Seite führt dich von null bis zu einem ersten Lauf.
Es dauert etwa fünfzehn Minuten, einmalig.

## 1. Python installieren {#install-python}

Dieses Werkzeug braucht **Python 3.10 oder neuer**.

- **Windows:** Lade Python von [python.org/downloads](https://www.python.org/downloads/)
  herunter und starte das Installationsprogramm. Setze auf dem ersten Bildschirm das
  Häkchen bei **Add python.exe to PATH**, dann klicke auf **Install Now**.
- **macOS und Linux:** Python 3 ist oft schon vorhanden. Wo diese Seiten `python`
  schreiben, tippe `python3`. (Battlefield 6 selbst läuft unter Windows; das Werkzeug
  liest seine Dateien, wo immer sie liegen.)

## 2. Dieses Werkzeug holen {#get-this-tool}

Öffne [github.com/Holdi601/3DHeat-Ext-Battlefield](https://github.com/Holdi601/3DHeat-Ext-Battlefield),
klicke auf den grünen Button **Code**, dann auf **Download ZIP**, und entpacke es in einen
Ordner deiner Wahl. Wenn du git benutzt: `git clone https://github.com/Holdi601/3DHeat-Ext-Battlefield`.

## 3. 3DHeat GameFiles kommt mit {#dheat-gamefiles-comes-with-it}

Das Werkzeug liest mit [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/)
(dessen glTF-Schreiber, der Steam-Bibliothekssuche und dem Oodle-Lader). Schritt 5
installiert es für dich. Ohne pip, also aus einem heruntergeladenen Ordner, den du direkt
startest, legst du GameFiles neben dieses Werkzeug als `3DHeat-GameFiles`, oder du setzt
`HEAT3D_GAMEFILES` auf seinen Ordner. Innerhalb eines 3DHeat-Checkouts
(`exporters/ext/battlefield-maps`) wird es von selbst in `exporters/gamefiles` gefunden.

## 4. Ein Terminal in diesem Ordner öffnen {#open-a-terminal-in-that-folder}

Ein Terminal ist ein Fenster, in das du Befehle tippst.

- **Windows:** Öffne den Ordner im Explorer, klicke in die Adressleiste, tippe
  `powershell` und drücke Enter. Ein blaues oder schwarzes Fenster öffnet sich, schon in
  diesem Ordner.
- **macOS:** Öffne **Terminal**, tippe `cd ` (mit Leerzeichen), zieh den Ordner ins
  Fenster und drücke Enter.

`cd` heißt „Ordner wechseln“: `cd C:\Tools\3DHeat-Ext-Battlefield` geht in diesen Ordner.

## 5. Das Werkzeug installieren {#install-the-tool}

Tippe dies und drücke Enter:

```bash
python -m pip install -e .
```

Am Ende solltest du sehen: `Successfully installed heat3d-ext-battlefield-...`
(und `heat3d-gamefiles-...` dazu).

## 6. Starten {#run-it}

```bash
heat3d-battlefield-maps levels
```

Du solltest etwa so etwas sehen:

```text
<n> levels in D:\Games\Steam\steamapps\common\Battlefield 6
  <level>                                    <size>  Data
  ...
```

Weiter: [Battlefield-6-Level](level-battlefield.md).

## So liest du die Befehle auf diesen Seiten {#how-to-read-the-commands-on-these-pages}

| Du siehst | Es bedeutet |
|---|---|
| `<level>` | ein Platzhalter: tippe stattdessen deinen eigenen Wert, ohne die `< >` |
| `[--textures [PIXELS]]` | optional: lass es weg, oder tippe es so, wie gezeigt |
| `# a note` | ein Kommentar für dich: nicht eintippen |
| `"C:\My Files\x"` | einen Pfad mit Leerzeichen setzt du in Anführungszeichen |

## Wenn etwas schiefgeht {#when-something-goes-wrong}

| Die Meldung | Was zu tun ist |
|---|---|
| `'python' is not recognized` | Python ist nicht installiert, oder das PATH-Kästchen war nicht angehakt: installiere es neu und hake es an (oder tippe `py` statt `python`). |
| `'heat3d-battlefield-maps' is not recognized` | Führe Schritt 5 im Ordner des Werkzeugs noch einmal aus, oder tippe `python -m heat3d_ext_battlefield` statt `heat3d-battlefield-maps`: es macht dasselbe. |
| `needs 3DHeat GameFiles: ...` | Schritt 5 hat es nicht installiert, oder du startest den Ordner direkt: siehe Schritt 3. |
| `no Frostbite game found in ...` | Installiere das Spiel, oder gib seinen Ordner an: `--install "D:\Games\Battlefield 6"`. |
| `no Oodle library found` | Ein Teil der Daten ist mit Oodle komprimiert; das Spiel liefert die Bibliothek (`oo2core_*.dll`), die sie entschlüsselt. Setze `HEAT3D_OODLE` auf diese Datei (siehe [Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html)). |
| alles andere | Lies die letzte Zeile der Meldung und eröffne damit ein Issue auf GitHub. |

Jeder Befehl endet außerdem mit einem **Exit-Status**: 0 heißt, es hat geklappt; 2 heißt,
dass das Spiel, die Datei oder GameFiles nicht gefunden wurde; 1 heißt, dass das Lesen
fehlschlug. Um ihn zu sehen, tippe `echo $LASTEXITCODE` in PowerShell oder `echo $?` unter
macOS und Linux.
