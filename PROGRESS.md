# PROGRESS.md — estado del desarrollo de Fugit

Fichero de relevo entre sesiones y agentes. Cada agente lo actualiza al terminar un bloque
de trabajo. Lo más reciente arriba en "Diario".

## Estado actual

- Fase en curso: 0 — Arranque del repositorio
- Agente de la última sesión: —
- Siguiente paso: crear `project.yml` (XcodeGen), la app vacía y los seis paquetes con un test cada uno; CI en GitHub Actions.

## Fases

- [ ] 0. Arranque: XcodeGen, app vacía que arranca en el simulador, paquetes y CI.
- [ ] 1. Núcleo BLE y ERG: SB20 y HRM-Dual, lectura de datos, ERG fijo, grabación a 1 Hz, modo demo.
- [ ] 2. Entrenos y ficheros: `.zwo` ida y vuelta, `.erg`/`.mrc`, motor de entrenos, HUD 2D, exportación `.fit`.
- [ ] 3. Cuentas: intervals.icu (plan de hoy y subida), Strava OAuth y subida, TrainingPeaks guiado, cola de subidas, pantalla Cuentas.
- [ ] 4. Ruta y mundo 3D: carga de `route.json`, carretera y terreno, física, simulación de pendiente, cámaras.
- [ ] 5. Bici, avatar y pulido: modelos originales, animación de pedaleo, iluminación, sonido, pantalla Resumen.

## Pruebas manuales pendientes del usuario

(El agente añade aquí la lista al cerrar cada fase.)

## Decisiones tomadas durante el desarrollo

(Decisiones técnicas nuevas que no están en SPEC.md, con fecha y motivo.)

## Problemas abiertos

—

## Diario

- 2026-11-24 — Repositorio creado con AGENTS.md, CLAUDE.md, SPEC.md, PROGRESS.md, `.gitignore`, plantilla de secretos y `Tools/route-builder`.
