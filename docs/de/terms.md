---
title: "Bedingungen und Lizenz"
nav_order: 8
lang: "de"
source: terms.md
source_hash: "81e5e54e5585"
nav_exclude: true
search_exclude: true
---
# Bedingungen und Lizenz {#terms-and-licence}

Diese Seite hält fest, was die Lizenzen sagen. Sie ist keine Rechtsberatung.

## EAs Spiel {#eas-game}

Battlefield 6 und seine Levels gehören Electronic Arts, das dieses Projekt nicht unterstützt.
Das Werkzeug enthält nichts vom Spiel und lädt nichts herunter: Es liest die Dateien der
Kopie, die **du** installiert hast, auf deinem Rechner, außerhalb des Spiels. Es ändert nichts
am Spiel, läuft nicht neben ihm und spricht mit keinem Server.

Wofür du es einsetzt, bleibt deine Verantwortung. Spiele haben eigene Lizenzbedingungen, und
EULAs verbieten oft Reverse Engineering. Das sind durchsetzbare Verträge, und die Pflicht
liegt bei dem, der das Werkzeug ausführt. Es zu nutzen ist deine Entscheidung, unter den
Bedingungen, die du für das Spiel und den Shop akzeptiert hast, in dem du es gekauft hast
(EAs Nutzungsbedingungen und die von Steam, der EA-App oder Epic).

Das Level, das es schreibt, ist Inhalt des Spieleherausgebers: Behalte exportierte `.glb`-Dateien
und die Texturen darin für deine eigene Analyse. Veröffentliche, teile oder verkaufe exportierte
Levels, Modelle oder Texturen nicht. Die `.gitignore` des Repositorys hält Spieldateien und
Exporte nach Dateityp aus der Versionsverwaltung heraus.

Darum ist es ein eigenes Paket: Wenn EA verlangt, dass es verschwindet, geht nur dieses Paket.
Der Viewer, GameFiles und die anderen Werkzeuge bleiben.

## Verschlüsseltes wird nicht geöffnet {#nothing-encrypted-is-opened}

- **Keine Schlüssel: keine mitgeliefert, keine rekonstruiert.** Nichts durchsucht eine
  ausführbare Datei nach einem Schlüssel, und nichts liest den Speicher eines anderen Prozesses.
- **Verschleierung ist ebenfalls nicht umgesetzt.** Die XOR-verschleierten Tabellen von
  Frostbite behalten ihren Schlüssel in der Datei selbst. Sie sind also eher Verschleierung als
  eine Zugangssperre. Sie werden trotzdem erkannt und abgelehnt, weil keine vorliegende Datei
  diese Form nutzt und es nichts gäbe, woran man eine Umsetzung prüfen könnte.
- **Verschlüsselte Dateien bleiben zu.** Das anfängliche Dateisystem von Battlefield 6, das die
  Typbibliothek des Spiels enthält, ist verschlüsselt und wird nicht gelesen. Der Level-Export
  arbeitet mit den nicht verschlüsselten Dateien und legt die zwei Typen, die er braucht, aus
  den Daten selbst an.
- **Nichts wird in einen Spielprozess eingeschleust.** Das Einschleusen in einen Titel mit
  Anti-Cheat riskiert das Konto dessen, der es ausführt.

## Oodle wird gefunden, nicht mitgeliefert {#oodle-is-found-not-bundled}

Ein Teil der Daten des Spiels ist mit Oodle komprimiert. Oodle (RAD Game Tools, jetzt Epic) ist
proprietär und hat kein weitergabefähiges Build. `oo2core_*.dll` ist an das Produkt lizenziert,
das sie ausliefert. Dieses Werkzeug liefert sie deshalb nie mit: `oodle.py` aus 3DHeat GameFiles
lädt eine Bibliothek, die schon auf dem Rechner liegt, die, die das Spiel mitbringt, oder die
Kopie, auf die `HEAT3D_OODLE` zeigt, statt eine eigene mitzuführen. Siehe
[Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html).

## Das Format selbst {#the-format-itself}

Frostbites `.toc`, Bundles, EBX-Partitionen, MeshSets und das Gelände sind nicht dokumentiert.
Sie zu lesen heißt, einen Container per Reverse Engineering zu öffnen. Die Leser hier wurden
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
