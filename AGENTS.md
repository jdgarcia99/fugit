# AGENTS.md — Fugit

Instrucciones permanentes para cualquier agente de código que trabaje en este repositorio
(Claude Code, Codex u otro). Léelas enteras antes de tocar nada.

## Qué es Fugit

App nativa de iPad, de uso personal y sin servidor propio, para entrenar en una smart bike
Stages SB20 sobre una única ruta 3D inspirada en el perfil de Tempus Fugit, ejecutar
entrenamientos estructurados `.zwo` en modo ERG y subir la actividad `.fit` a Strava,
intervals.icu y (de forma guiada) TrainingPeaks.

La especificación completa está en `SPEC.md`. Es la fuente de verdad: si algo de este
fichero o de una petición contradice `SPEC.md`, para y pregunta.

## Protocolo de trabajo (obligatorio en cada sesión)

Este proyecto puede pasar de un agente a otro a mitad de una fase (por ejemplo, de
Claude Code a Codex cuando se acaba el uso). Por eso el estado vive en el repo, no en
tu memoria.

1. Al empezar: lee `AGENTS.md`, `SPEC.md` y `PROGRESS.md`, y mira `git log --oneline -20`
   y `git status`. Continúa desde "Siguiente paso" de `PROGRESS.md`.
2. Trabaja en bloques pequeños y verificables. Tras cada bloque que compile y pase tests,
   haz commit (Conventional Commits en inglés: `feat(ble): ...`, `fix(zwo): ...`).
3. Antes de terminar la sesión, o si notas que te quedas sin contexto o sin uso:
   actualiza `PROGRESS.md` (estado, qué funciona, qué falta, siguiente paso concreto,
   decisiones tomadas, problemas abiertos) y haz commit. Nunca dejes trabajo sin commitear.
4. Al cerrar cada fase del plan, detente y entrega al usuario una lista de pruebas
   manuales con la SB20 y el iPad. No empieces la fase siguiente hasta que confirme.
5. Pregunta antes de: añadir dependencias externas, cambiar una decisión de `SPEC.md`,
   instalar herramientas globales o hacer algo que cueste dinero o requiera cuentas.

## Entorno

- Mac con Xcode 26 y SDK de iPadOS 26. Destino de despliegue: iPadOS 26.0.
- Dispositivo objetivo: iPad Pro de 11" en horizontal (2388×1668 y 2420×1668 px);
  la interfaz debe adaptarse a pantallas mayores.
- Proyecto Xcode generado con XcodeGen (`project.yml` en git, `.xcodeproj` ignorado),
  para que ningún agente edite `project.pbxproj` a mano. Si XcodeGen no está instalado,
  pide permiso para `brew install xcodegen`.
- Compilar: `xcodegen && xcodebuild -scheme Fugit -destination 'generic/platform=iOS Simulator' build`.
- Tests de paquetes: `swift test` dentro de cada paquete (deben correr en macOS sin hardware).
- Python 3 solo para `Tools/` (`pip install -r Tools/route-builder/requirements.txt`).

## Arquitectura

```
App/                     SwiftUI: pantallas Inicio, Dispositivos, Biblioteca, Sesión (HUD), Resumen, Ajustes/Cuentas
Packages/
  FugitBLE/              Core Bluetooth: FTMS (0x1826), CPS (0x1818), HR (0x180D), cola de órdenes con confirmación
  FugitWorkouts/         Modelo de entreno, parser/escritor .zwo, import .erg/.mrc, motor ERG
  FugitFIT/              Exportación .fit (cycling / virtual_activity, 1 Hz, FC y RR)
  FugitPhysics/          Modelo de potencia → velocidad a 20 Hz, pendiente desde route.json
  FugitWorld/            RealityKit: carretera, terreno, cámara, bici y avatar; carga de route.json
  FugitAccounts/         Strava (OAuth), intervals.icu (clave API), TrainingPeaks guiado, cola de subidas, Llavero
Tools/route-builder/     Python: .fit de Zwift → route.json (ya funciona, no lo reescribas sin motivo)
Config/                  xcconfig; Secrets.xcconfig fuera de git
Assets/                  Modelos USDZ y texturas propias o CC0
```

Reglas de diseño:

- La lógica (BLE parsing, .zwo, física, .fit, cola de subidas) no depende de UIKit ni de
  RealityKit y se prueba con Swift Testing en macOS. El hardware se abstrae tras protocolos
  (`TrainerControlling`, `HeartRateSource`) con implementaciones simuladas para tests y
  para un "modo demo" sin bici.
- Concurrencia: Swift 6 con comprobación estricta; actores para BLE y la sesión.
- Persistencia: SwiftData (`Workout`, `Session`, `Sample` a 1 Hz, `Settings`).
- Tokens y claves solo en el Llavero de iOS, nunca en UserDefaults ni en logs.
- UI en español. Código, identificadores, comentarios y commits en inglés.
  `PROGRESS.md` en español.

## Detalles críticos

- SB20: control por FTMS estándar. Secuencia `Request Control` → `Start/Resume` → órdenes;
  esperar la indicación de respuesta del Control Point (0x2AD9) y reintentar una vez a 1 s.
  ERG con `Set Target Power` (0x05); simulación con `Set Indoor Bike Simulation Parameters`
  (0x11) a 2–4 Hz; pendientes negativas se envían como 0 % (la SB20 no simula bajadas).
  Los cambios del manillar los gestiona la bici: no implementar cambios virtuales.
- Pulsómetro: Garmin HRM-Dual, admite una sola conexión Bluetooth a la vez. Recordar el
  periférico por identificador y no emparejar otras bandas cercanas.
- Reconexión: si no llegan datos en 3 s, la sesión sigue (el avatar frena con la física),
  se reintenta la conexión y el ERG se reanuda en el paso en curso. Guardado cada 30 s.
- `.zwo`: debe ser compatible ida y vuelta con Zwift. Conservar elementos desconocidos al
  reexportar. Tests con ficheros reales de ejemplo en `Packages/FugitWorkouts/Tests/Fixtures`.
- `.fit`: validar en tests decodificando el fichero generado (por ejemplo con
  `fitdecode` desde un test de integración en Python, o el SDK oficial de Garmin).
- intervals.icu: `GET /api/v1/athlete/{id}/events` para el plan, descarga `.zwo` del evento,
  `POST /api/v1/athlete/{id}/activities` para subir. Autenticación básica con la clave API.
- Strava: OAuth con `ASWebAuthenticationSession`, esquema `fugit://strava-callback`,
  scopes `activity:write,read`, subida `POST /api/v3/uploads` (`data_type=fit`,
  `trainer=1`, `sport_type=VirtualRide`, `external_id` = UUID de sesión) y sondeo de
  `/uploads/{id}`. Client ID y secret desde `Config/Secrets.xcconfig` vía Info.plist.
- TrainingPeaks: su API no está disponible para uso personal. No uses su API interna ni
  cookies de sesión. La subida es guiada: abrir su web en una vista segura para adjuntar
  el `.fit`. El plan llega a intervals.icu mediante tp2intervals (fuera de la app).
- Ruta: `route.json` lo genera `Tools/route-builder` a partir de un `.fit` del usuario;
  formato `points = [distancia_m, x_este_m, y_norte_m, altitud_m, pendiente_pct]` cada 2 m,
  con secciones `lead_in` y `lap`. La app lo carga desde Archivos o desde el bundle local.

## Prohibido

- Usar, extraer o imitar fielmente modelos, texturas, mundos, nombres de rutas o marcas de
  Zwift, la "Tron Bike" o Rapha. La bici y la equipación son diseños originales (ver SPEC.md).
  En la UI la ruta se llama "Fugit" o "Desierto", no "Tempus Fugit" ni "Watopia".
- Conectarse a servidores de Zwift o de TrainingPeaks de forma no oficial.
- Commitear secretos, `Secrets.xcconfig`, ficheros `.fit`, `route.json` o datos personales.
  El repositorio es público.
- Desactivar tests o comprobaciones de concurrencia para que algo compile.

## Definición de "hecho" para cada tarea

Compila sin warnings nuevos, los tests pasan, hay tests para la lógica nueva, `PROGRESS.md`
está actualizado y el commit está hecho.
