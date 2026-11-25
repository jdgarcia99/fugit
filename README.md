# Fugit

App personal de iPad para entrenar en una smart bike Stages SB20: entrenos `.zwo` en ERG,
una ruta 3D llana en el desierto y subida de actividades `.fit` a Strava e intervals.icu.

Proyecto personal sin relación con Zwift, Stages, Garmin, Strava ni TrainingPeaks.

- Especificación: [SPEC.md](SPEC.md)
- Estado del desarrollo: [PROGRESS.md](PROGRESS.md)
- Instrucciones para agentes de código: [AGENTS.md](AGENTS.md)

## Requisitos

- Xcode 26, iPadOS 26, XcodeGen
- Python 3 para `Tools/route-builder`

## Generar la ruta

```
pip install -r Tools/route-builder/requirements.txt
python Tools/route-builder/route_builder.py mi_salida.fit -o route.json
```

`route.json` y los `.fit` no se suben al repositorio.
