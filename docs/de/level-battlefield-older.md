---
title: Level aus Battlefield 4 und Battlefield 1
---

# Level aus Battlefield 4 und Battlefield 1

`levels` und `level` lesen auch Battlefield 4 und Battlefield 1. Gib den Ordner
des Spiels mit `--game` an (oder setze `HEAT3D_BATTLEFIELD_GAME`); nach diesen
beiden Spielen sucht das Werkzeug nicht von selbst.

```bash
heat3d-battlefield-maps levels --game "<der Battlefield-4-Ordner>"
heat3d-battlefield-maps level MP_Prison --game "<der Battlefield-4-Ordner>"
heat3d-battlefield-maps level all --game "<der Battlefield-1-Ordner>" -o levels/battlefield-1
```

- `levels` listet die Mehrspieler-Level auf, mit der Ebene, aus der jedes
  stammt (`Data`, `Patch`, `Update/<Paket>`).
- `level <Name>` schreibt ein Level als `<Level>.glb`, benannt wie das Spiel
  das Level nennt (`MP_Prison.glb`, `XP1_001.glb`). Ohne `-o` landet es in
  `$HEAT3D_LEVELS/battlefield-4/` (bzw. `battlefield-1`), wenn das gesetzt ist.
- `level all` schreibt jedes Mehrspieler-Level; `-o` ist dann ein Ordner. Mit
  `--order DATEI` kommen die in der Datei genannten Level (eines pro Zeile;
  es zählt das letzte Wort der Zeile) zuerst, in dieser Reihenfolge.
- `--detail-budget N` begrenzt die Dreiecke der platzierten Meshes
  (Standard 3.000.000).

Rechne mit 20 bis 60 Sekunden und 100 bis 130 MB pro Level; ein Level, dessen
Meshes ihre Puffer in anderen Teilen der Installation haben, braucht beim
ersten Mal ein paar Minuten länger.

## Was in der Datei steht

| Teil | Was |
|---|---|
| `ground:terrain` | das Höhenfeld: das Spielgebiet mit 1 bis 3 m, der Rest des Terrain-Quadrats gröber; in Battlefield 1 mit der Farbkarte des Spiels gefärbt, in Battlefield 4 nach Steigung |
| `structure:buildings`, `structure:props`, `structure:rocks`, `structure:trees`, `structure:infrastructure`, `water:water` | jedes Mesh, das das Level platziert, nach dem, was sein Asset-Pfad sagt, in flachen Farben |

Jeder Teilname endet auf ` @battlefield-4/<Level>` bzw. ` @battlefield-1/<Level>`.
Der 3DHeat-Viewer liest das: Ein einmal geladenes Level bleibt in seiner
Level-Bibliothek, und einer Tabelle, deren Spalte `map` dieses Level nennt,
wird es angeboten – und sie bekommt es von selbst, wenn kein Level geladen ist.

Positionen sind die des Spiels: x und z waagrecht, y nach oben, Meter.
In Spielkoordinaten aufgezeichnete Positionen liegen so, wie sie sind, auf dem Level. Die Level
wurden mit aufgezeichneten Positionen geprüft.

## Wie gelesen wird

Das ältere Frostbite hält jedes Level in einem Superbundle: eine `.toc`, die die
Bundles nennt, und eine `.sb`, die sie enthält; jedes Bundle ist ein Baum, der
seine Partitionen (`ebx`), Ressourcen (`res`) und Chunks per SHA-1 aufführt, und
`cas.cat`-Dateien sagen, welcher `cas_NN.cas`-Blob welchen Hash enthält. Patches
bringen eigene Tabellen mit; Inhalte, die ein Patch geändert hat, können als
Änderung des alten Inhalts gespeichert sein, die angewendet wird.
Erweiterungslevel von Battlefield 4 halten ihre Bundles vollständig in der `.sb`.

- **Partitionen** beschreiben sich selbst: Jede trägt die Namen ihrer Typen und
  Felder, das Layout des Levels liest sich also als benannte Objekte
  (`legacyebx.py`).
- **Was platziert wird**: Der Durchlauf beginnt bei der eigenen Partition des
  Levels und folgt Sub-Levels, World Parts, Ebenen, Prefabs und
  Objektreferenzen und verknüpft dabei ihre Transformationen; Static Model
  Groups platzieren den Großteil der Szenerie (`legacylevel.py`).
- **Wo die Kopien einer Static Model Group stehen**: für die meisten Mitglieder
  nicht in der Partition, sondern in der Kollisionsressource der Gruppe, einem
  Havok-Packfile; dessen Static Compound Shape hat einen Eintrag pro Kopie oder
  pro Physikteil (`legacyhavok.py`).
- **Meshes**: das MeshSet-Layout des jeweiligen Spiels (`legacymesh.py`); die
  teuersten Meshes gehen auf gröbere Detailstufen, bis das Budget hält, und
  passen selbst die gröbsten nicht, fallen die kleinsten Meshes weg.
- **Terrain**: der Quadtree der Höhenseiten im Streaming Tree
  (`legacyterrain.py`); jede Seite wird vor der Verwendung mit ihren Nachbarn
  und ihrer Elternseite abgeglichen.

Nichts wird entschlüsselt: Keine dieser Dateien ist verschlüsselt. Die Inhalte
beider Spiele sind LZ4-Blöcke oder unkomprimiert abgelegt; eine
Oodle-Bibliothek wird nicht gebraucht.

## Was fehlt

- Zerstörungszustände, Fahrzeuge, Soldaten, Effekte, Sound und Logik.
- Kopien einer Static Model Group ohne Kollision, wenn die Gruppe ihre
  Transformationen nirgends sonst ablegt.
- Erweiterungslevel von Battlefield 4: Wo ein Patch ein Bundle als Änderung
  speichert, wird das ungepatchte Bundle gelesen, und Meshes, deren Puffer nur
  der Patch hat, fehlen.
- Zwei Level von Battlefield 1 haben keine Terrain-Ressource; sie werden ohne
  Boden geschrieben.

Dieses Werkzeug steht in keiner Verbindung zu EA oder DICE; Marken gehören
ihren Inhabern.
