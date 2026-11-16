---
title: "Bedingungen und Lizenz"
nav_order: 8
lang: "de"
source: terms.md
source_hash: "50d8b31139d6"
nav_exclude: true
search_exclude: true
---
# Bedingungen und Lizenz {#terms-and-licence}

## EAs Spiel {#eas-game}

Battlefield 6 und seine Levels gehören Electronic Arts. 3DHeat Battlefield ist nicht mit
Electronic Arts verbunden und wird von Electronic Arts nicht unterstützt. Battlefield und die
zugehörigen Namen und Marken gehören ihren Inhabern.

Das Werkzeug liefert nichts vom Spiel mit und lädt nichts herunter: keine Spielinhalte, keinen
Spielcode, keine DLLs. Es liest die Dateien der Kopie, die **du** installiert hast, auf deinem
Rechner, außerhalb des Spiels. Es ändert nichts am Spiel, läuft nicht neben ihm und spricht mit
keinem Server.

Das Level, das es schreibt, bleibt auf deinem Rechner: Behalte exportierte `.glb`-Dateien und die
Texturen darin für deine eigene Analyse, und veröffentliche, teile oder verkaufe exportierte
Levels, Modelle oder Texturen bitte nicht. Die `.gitignore` des Repositorys hält Spieldateien und
Exporte nach Dateityp aus der Versionsverwaltung heraus.

Jeder Spiele-Leser ist ein eigenes kleines Projekt mit eigener Lizenzdatei, eigenen Releases und eigenem Issue-Tracker. So lässt er sich für sich allein installieren, aktualisieren und pflegen - oder auf Wunsch eines Rechteinhabers zurückziehen -, ohne dass der Viewer oder die anderen Werkzeuge davon berührt werden.

Rechteinhaber: Bitte ein Issue unter [github.com/Holdi601/3DHeat-Ext-Battlefield/issues](https://github.com/Holdi601/3DHeat-Ext-Battlefield/issues) eröffnen - wir antworten schnell und entfernen auf Anfrage alles.

## Verschlüsseltes wird nicht geöffnet {#nothing-encrypted-is-opened}

- **Keine Schlüssel: keine mitgeliefert, keine rekonstruiert.** Nichts durchsucht eine
  ausführbare Datei nach einem Schlüssel, und nichts liest den Speicher eines anderen Prozesses.
- **Verschleierung ist ebenfalls nicht umgesetzt.** Die XOR-verschleierten Tabellen von
  Frostbite werden erkannt und abgelehnt: Keine vorliegende Datei nutzt diese Form, und es gäbe
  nichts, woran man eine Umsetzung prüfen könnte.
- **Verschlüsselte Dateien bleiben zu.** Das anfängliche Dateisystem von Battlefield 6, das die
  Typbibliothek des Spiels enthält, ist verschlüsselt und wird nicht gelesen. Der Level-Export
  arbeitet mit den nicht verschlüsselten Dateien und legt die zwei Typen, die er braucht, aus
  den Daten selbst an.
- **Nichts wird in einen Spielprozess eingeschleust.** Das Werkzeug liest nur Dateien auf
  der Festplatte.

## Oodle wird gefunden, nicht mitgeliefert {#oodle-is-found-not-bundled}

Ein Teil der Daten des Spiels ist mit Oodle komprimiert. Oodle (RAD Game Tools, jetzt Epic) ist
proprietär und hat kein weitergabefähiges Build. `oo2core_*.dll` ist an das Produkt lizenziert,
das sie ausliefert. Dieses Werkzeug liefert sie deshalb nie mit: `oodle.py` aus 3DHeat GameFiles
lädt eine Bibliothek, die schon auf dem Rechner liegt, die, die das Spiel mitbringt, oder die
Kopie, auf die `HEAT3D_OODLE` zeigt, statt eine eigene mitzuführen. Siehe
[Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html).

## Das Format selbst {#the-format-itself}

Frostbites `.toc`, Bundles, EBX-Partitionen, MeshSets und das Gelände sind nicht dokumentiert. Die Leser hier wurden
anhand der eigenen Dateien von Battlefield 6 erarbeitet. Öffentliche Beschreibungen älterer
Frostbite-Versionen (die Frosty-Modding-Werkzeuge, eine Notiz zum Format von Need for Speed Heat,
ein GDC-Vortrag) lieferten Feldnamen und eine Karte, wonach man suchen muss. Kein Code wurde
von dort übernommen; jeder Offset wurde an den Dateien gemessen (die Quellen und ihre Lizenzen:
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md)).

## Lizenz und Quellen {#licence-and-sources}

MIT ([`LICENSE`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSE)):
benutzen, ändern, ausliefern, kommerziell oder nicht. Es baut auf
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (MIT) auf und braucht numpy
(BSD-3-Clause), Pillow (MIT-CMU), lz4 und zstandard (BSD-3-Clause); die Tests brauchen pytest
(MIT). Siehe [`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md).
