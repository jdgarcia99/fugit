# Prompts para desarrollar Fugit

Los agentes no dependen de la conversación: todo el contexto está en `AGENTS.md`, `SPEC.md` y
`PROGRESS.md`. Por eso los prompts son cortos y sirven igual para Claude Code que para Codex.

## Antes de empezar (una vez)

1. Crea el repositorio público `fugit` en GitHub y clónalo en el Mac.
2. Copia dentro el contenido de este paquete y haz el primer commit.
3. Copia `Config/Secrets.example.xcconfig` como `Config/Secrets.xcconfig` (no se sube a git).
   Los valores de Strava los rellenarás en la fase 3.
4. Guarda tu `route.json` fuera del repo (por ejemplo en iCloud Drive); se usará en la fase 4.
5. Abre la terminal en la carpeta del repo y lanza `claude` (o `codex`).

## 1. Prompt de arranque (primera sesión)

```
Vas a desarrollar Fugit, una app de iPad para entrenar con una Stages SB20.
Lee AGENTS.md, SPEC.md y PROGRESS.md enteros antes de nada y sigue el protocolo de trabajo de AGENTS.md.

Empieza por la fase 0 de PROGRESS.md:
- project.yml de XcodeGen con la app Fugit (iPadOS 26, solo iPad, horizontal) que arranca en el simulador con una pantalla de Inicio vacía.
- Los seis paquetes Swift de AGENTS.md, cada uno con un test mínimo que pase con swift test.
- Lectura de Config/Secrets.xcconfig en la build sin que falle si los valores están vacíos.
- Workflow de GitHub Actions que compile la app y ejecute los tests de los paquetes en macOS.

Antes de escribir código, enséñame el plan de la fase 0 y espera mi visto bueno.
Al terminar la fase, actualiza PROGRESS.md, haz commit y dame la lista de comprobaciones manuales.
```

## 2. Prompt para continuar (cualquier sesión nueva, mismo agente u otro)

```
Retoma el desarrollo de Fugit. Lee AGENTS.md, SPEC.md y PROGRESS.md, revisa git log -20 y git status,
y continúa desde el "Siguiente paso" de PROGRESS.md siguiendo el protocolo de AGENTS.md.
Si hay trabajo a medias sin commitear, revísalo primero y dime qué encontraste.
Dime en una frase qué vas a hacer antes de empezar.
```

## 3. Prompt de relevo a Codex (cuando se acaba el uso de Claude Code)

Antes de cerrar Claude Code, si aún puedes, envíale:

```
Me voy a cambiar de agente. Actualiza PROGRESS.md con el estado exacto, lo que estabas haciendo,
los ficheros a medio tocar y el siguiente paso concreto, y haz commit ahora.
```

Después, en Codex (que lee AGENTS.md de forma automática):

```
Este proyecto lo venía desarrollando otro agente. Lee AGENTS.md, SPEC.md y PROGRESS.md,
revisa git log -20 y git status, y continúa desde el "Siguiente paso" de PROGRESS.md.
Sigue el protocolo de AGENTS.md al pie de la letra, incluido actualizar PROGRESS.md y hacer commit
al acabar cada bloque. Antes de cambiar nada, resúmeme en tres líneas dónde está el proyecto.
```

Para volver a Claude Code más tarde, usa el prompt 2.

## 4. Prompt para cerrar una fase y pasar a la siguiente

```
He hecho las pruebas manuales de la fase N con la SB20 y el iPad. Resultado:
<pega aquí lo que funcionó y lo que falló>
Corrige los fallos, marca la fase como completada en PROGRESS.md y prepara el plan de la fase N+1.
Enséñame el plan antes de escribir código.
```

## Consejos

- Una fase por sesión como máximo; si la fase es grande, pide que la divida en bloques.
- Para la fase 1 deja la SB20 encendida y cerca del Mac/iPad: el agente no puede probar el Bluetooth real,
  así que te pedirá que ejecutes la app en el iPad y le cuentes lo que ves.
- Si un agente propone cambiar algo de SPEC.md, que lo apunte en "Decisiones tomadas" de PROGRESS.md.
