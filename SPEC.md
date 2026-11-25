# Especificación — Fugit

App nativa de iPad, de uso personal y sin servidor, para entrenar con la Stages SB20 en una
única ruta inspirada en Tempus Fugit, ejecutar entrenamientos estructurados en ERG y subir
la actividad. Repositorio público `fugit` en GitHub.

## 1. Alcance

**Dentro de la v1**

- Conexión Bluetooth a la Stages SB20: potencia, cadencia, control de resistencia (ERG y simulación de pendiente).
- Pulsómetro Garmin HRM-Dual por Bluetooth.
- Lectura y escritura de entrenamientos `.zwo` (formato de Zwift) e importación de `.erg` y `.mrc`.
- Exportación de actividades `.fit` que aceptan Strava, TrainingPeaks, intervals.icu y Garmin Connect.
- Importación de los entrenamientos planificados de TrainingPeaks a través de intervals.icu.
- Subida automática a Strava e intervals.icu y guiada a TrainingPeaks.
- Un mundo 3D original: una ruta llana en bucle con el perfil de Tempus Fugit.
- Una bici original estilo neón y un avatar adulto con equipación de club original.
- Un solo usuario, sin multijugador.

**Fuera de alcance**

- Servidores de Zwift, otros ciclistas, eventos.
- Modelos, texturas o mundos de Zwift, y marcas de terceros (Tron Bike, Rapha).
- Más rutas, más bicis, logros, nivel o tienda.
- Android, Apple TV o Mac.

## 2. Plataforma y arquitectura

- iPadOS 26 como mínimo; optimizado para iPad Pro de 11" en horizontal (2388×1668 y 2420×1668 px), adaptable a pantallas mayores.
- Swift 6, SwiftUI, Core Bluetooth, RealityKit, SwiftData, Swift Concurrency (bucle de simulación a 20 Hz).
- Una web o PWA no sirve: Safari en iPad no soporta Web Bluetooth.

Flujo de datos: SB20 y HRM-Dual → `FugitBLE` → sesión (motor de entrenos + física) → render 3D y HUD;
la sesión graba a 1 Hz → `.fit` → `FugitAccounts` → intervals.icu, Strava y TrainingPeaks (guiado).
Archivos/iCloud para importar `.zwo` y guardar `.fit`. El plan de TrainingPeaks llega a intervals.icu
mediante tp2intervals en un Docker del usuario, fuera de la app.

Estructura del repositorio: ver `AGENTS.md`.

## 3. Conexión con la Stages SB20 y el pulsómetro

| Servicio BLE | UUID | Uso |
| --- | --- | --- |
| Fitness Machine (FTMS) | 0x1826 | Indoor Bike Data (0x2AD2: potencia, cadencia, velocidad) y Control Point (0x2AD9) |
| Cycling Power (CPS) | 0x1818 | Respaldo de potencia y cadencia si FTMS falla |
| Heart Rate | 0x180D | HRM-Dual: FC e intervalos RR (0x2A37) |
| Device Information | 0x180A | Modelo y firmware para el registro |

Control de resistencia (FTMS Control Point):

- ERG: `Set Target Power` (op 0x05) en cada paso; rampas en escalones de 1 s.
- Simulación: `Set Indoor Bike Simulation Parameters` (op 0x11) con pendiente, Crr, CdA y viento, a 2–4 Hz según la posición en la ruta. La SB20 no simula bajadas: pendientes negativas se envían como 0 %.
- Nivel fijo: `Set Target Resistance Level` (op 0x04) para rodar libre.
- Secuencia: `Request Control` → `Start/Resume` → órdenes. Cada orden espera su indicación de respuesta; un reintento si no llega en 1 s.

Cambios de marcha: los gestiona la propia SB20 (configuración en la app de Stages). No hay cambios virtuales.

Pulsómetro HRM-Dual (pack del Garmin Edge 1040): emite por ANT+ y Bluetooth a la vez, pero por
Bluetooth admite una sola conexión. Si el Edge también graba, debe usarla por ANT+. La app recuerda el
periférico por identificador y no empareja otras bandas. Si se pierde la FC, la sesión sigue y se reconecta.

Reconexión de la SB20: si no llegan datos en 3 s, el avatar frena con la física, la app reintenta sin
cortar la actividad y el ERG se reanuda en el paso en curso.

## 4. Ficheros compatibles con Zwift

| Fichero | Dirección | Detalle |
| --- | --- | --- |
| `.zwo` (XML) | Importar y exportar | Entrenos estructurados; potencias relativas al FTP |
| `.fit` | Exportar (e importar para historial) | Potencia, cadencia, FC, RR, velocidad, distancia, altitud a 1 Hz |
| `.erg` / `.mrc` | Importar | Se convierten a `.zwo` internamente |

Elementos `.zwo` soportados: `Warmup`, `Cooldown`, `Ramp`, `SteadyState`, `IntervalsT` (`OnPower`,
`OffPower`, `OnDuration`, `OffDuration`, `Repeat`), `FreeRide`, `MaxEffort`, `textevent`, cadencia
objetivo, `name`, `author`, `description`, `sportType`, `tags`. Los elementos desconocidos se conservan
al reexportar y se ignoran al ejecutar, con aviso.

Acceso a ficheros: `UIDocumentPicker` desde Archivos (iCloud Drive, SMB, Dropbox), tipos registrados
para "Abrir con…", y una carpeta persistente opcional mediante marcador con ámbito de seguridad.

El `.fit` exportado usa `sport=cycling`, `sub_sport=virtual_activity`, coordenadas de la ruta y altitud
del perfil.

## 5. Plan de entrenamiento (TrainingPeaks vía intervals.icu)

La API de TrainingPeaks no se concede para uso personal. El usuario no tiene TrainingPeaks Premium.

1. El plan se publica en TrainingPeaks.
2. tp2intervals (Docker del usuario) copia los planificados a intervals.icu (con cuenta gratuita: hoy y mañana).
3. Fugit consulta `GET /api/v1/athlete/{id}/events?oldest=<hoy>&newest=<hoy+7>` con la clave API de intervals.icu.
4. Descarga cada entreno como `.zwo`, lo muestra en "Plan de hoy" y lo ejecuta en ERG.

Respaldo siempre disponible: descargar el `.zwo`/`.erg`/`.mrc` desde TrainingPeaks y abrirlo desde Archivos.
El FTP se toma de intervals.icu si está conectado, o del ajuste manual.

## 6. Cuentas y subida de actividades

| Cuenta | Conexión | Subida | Credenciales |
| --- | --- | --- | --- |
| Strava | OAuth 2.0 con app de API propia (scopes `activity:write,read`) | Automática: `POST /api/v3/uploads` (`data_type=fit`, `trainer=1`, `sport_type=VirtualRide`, `external_id` = UUID de sesión) y sondeo de `/uploads/{id}` | Access token (6 h) y refresh token en el Llavero |
| intervals.icu | Clave API personal + id de atleta | Automática: `POST /api/v1/athlete/{id}/activities` | Clave en el Llavero |
| TrainingPeaks | Sin API | Guiada: botón que abre su web en una vista segura para adjuntar el `.fit`; se marca como subido al confirmar | Ninguna |

Pantalla Cuentas (en Ajustes): estado de cada cuenta, atleta y última subida; Conectar, Reconectar y
Desconectar (borra tokens y en Strava revoca con `POST /oauth/deauthorize`); subida automática por cuenta
y opción "Preguntar al terminar".

OAuth de Strava: `ASWebAuthenticationSession` con esquema `fugit://strava-callback`. Como el repo es
público, client ID y secret van en `Config/Secrets.xcconfig` (ignorado por git) con plantilla
`Secrets.example.xcconfig`.

Cola de subidas: una tarea por cuenta y sesión (pendiente, subiendo, hecha, error); reintentos con espera
creciente sin conexión o con errores 5xx, y al reabrir la app; un duplicado de Strava se marca como hecho.
El Resumen muestra el estado, enlace a la actividad y botón Reintentar.

## 7. Ruta

Perfil de Tempus Fugit: vuelta de 17,3 km, unos 16 m de desnivel oficial, acceso de unos 2,4 km, ida y
vuelta casi llana con giro en el extremo, bucle final antes del arco de meta y sprint de 500 m en falso llano.

`route.json` se genera con `Tools/route-builder` desde un `.fit` propio del usuario (ya validado: vuelta
detectada de 17,31 km, error medio 2,9 m, altitud 12,7–17,5 m, pendientes entre −1,6 % y +1,7 %). Formato:

```json
{
  "name": "Tempus Fugit",
  "origin_latlon": [lat, lon],
  "format": "points = [distancia_m, x_este_m, y_norte_m, altitud_m, pendiente_pct]",
  "step_m": 2.0,
  "lead_in": { "length_m": 2400, "elevation_gain_m": 0, "points": [[...], ...] },
  "lap":     { "length_m": 17310, "elevation_gain_m": 23, "points": [[...], ...] },
  "landmarks": [{ "name": "Meta (arco)", "lap_m": 0 }]
}
```

`route.json` no se sube al repositorio. La app lo carga desde Archivos (o un bundle local ignorado por git).
Alternativa sin `.fit`: el stream del segmento público de Strava.

Mundo 3D original: desierto llano, carretera de 2 carriles generada con spline Catmull–Rom, arco de meta,
pueblo del oeste con estación y tren, cañón rocoso con oasis y cascada, pueblo-balneario de los años 50 en el
giro, ruinas en el acantilado en el bucle final, ciclo de luz configurable. Modelos low-poly propios o CC0
(Kenney, Poly Haven, Quaternius).

Modos: vueltas infinitas, número de vueltas, o ruta como fondo de un entreno ERG (la pendiente no se envía).

## 8. Bici y avatar (diseños originales)

- Bici "Neón": cuadro aero negro mate con líneas de luz emisiva cian, ruedas lenticulares con anillo
  luminoso que pulsa con la cadencia, brillo según potencia (bloom). Masa 7,5 kg; CdA y Crr editables.
- Avatar adulto con esqueleto humanoide estándar; pedaleo procedural sincronizado con la cadencia real,
  sprint de pie por encima de un umbral de potencia. Equipación de club original: azul marino con franja
  en el pecho y detalles en rosa, casco y gafas sin marcas; colores editables.
- Modelos en Blender (avatar base MakeHuman CC0), exportados a USDZ.

## 9. Pantallas y HUD

| Pantalla | Contenido |
| --- | --- |
| Inicio | Plan de hoy, Rodar libre, biblioteca, estado de SB20 y pulsómetro |
| Dispositivos | Búsqueda BLE, dispositivos recordados, batería, firmware |
| Biblioteca | Entrenos con gráfico de bloques, duración, TSS e IF estimados |
| Resumen | Gráficas de potencia y FC, medias, NP, TSS, zonas; estado de subidas |
| Ajustes | Perfil (FTP, FC máx., peso, altura), Cuentas, equipación |

HUD: potencia (media 3 s) grande, FC, cadencia, velocidad, distancia, tiempo, W/kg; bloque actual con
objetivo y cuenta atrás, gráfico de bloques y mensajes `textevent`; perfil de la ruta con posición y
próximo hito; controles de pausa, saltar bloque, ±5 % de ERG, modo simulación y cámara (persecución,
lateral, primera persona). Toques grandes, uso desde el manillar. Colores de zonas habituales.

## 10. Física y datos

Velocidad a 20 Hz: `P·η = (m·g·sinθ + Crr·m·g·cosθ + ½·ρ·CdA·v²)·v + m·v·dv/dt`
con m = peso + 7,5 kg, Crr 0,004, CdA 0,26 m², ρ 1,225 kg/m³, η 0,98. Sin rebufo; viento 0 por defecto.

SwiftData: `Workout` (origen, XML original, bloques), `Session` (fecha, entreno, vueltas, resumen, `.fit`,
estado de subidas), `Sample` a 1 Hz (tiempo, potencia, cadencia, FC, RR, velocidad, distancia, altitud,
pendiente, objetivo ERG), `Settings`. Guardado cada 30 s y recuperación de sesiones interrumpidas.

## 11. Plan por fases

0. Arranque del repo y CI.
1. Núcleo BLE y ERG (ya útil para entrenar sin 3D).
2. `.zwo`, motor de entrenos, HUD 2D, `.fit`.
3. intervals.icu, Strava, TrainingPeaks guiado, cola de subidas.
4. Ruta y mundo 3D, física, simulación de pendiente.
5. Bici, avatar y pulido.

## 12. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| tp2intervals depende de la sesión web de TrainingPeaks | Importación manual de `.zwo` siempre disponible |
| Reenvíos FTMS y reinicios de la SB20 | Cola de órdenes con confirmación, reintentos, reconexión sin cortar |
| Rendimiento 3D durante 1–2 h | 60 fps con bajada a 30, LOD, modo de bajo consumo, iPad enchufado |
| Firma gratuita caduca a 7 días | Apple Developer Program o recompilar desde el Mac |
