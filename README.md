# PsicoseadoSSTool

Launcher gráfico de herramientas para screenshare y análisis forense en Windows 10/11 x64.

[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)
[![Tests](https://github.com/Psicoseado/PsicoseadoSSTool/actions/workflows/tests.yml/badge.svg)](https://github.com/Psicoseado/PsicoseadoSSTool/actions/workflows/tests.yml)

> Utiliza esta aplicación únicamente en equipos propios o con autorización
> explícita. Varias funciones solicitan permisos de administrador y ejecutan
> software de terceros.

## Interfaz

- Navegación superior dividida por separadores.
- Botón de lupa que abre `https://github.com/Psicoseado`.
- Selector compacto EN/ES en la cabecera; inglés es siempre el idioma inicial.
- Categorías: Orbdiff/Others, MeowTonynoh, Spokwn, Scripts, Others Tools y Dependencies.
- Tarjetas completas clicables, animaciones de transición y cooldown visible de cinco segundos.
- Ventana redimensionable, minimizado normal a la barra de tareas e intro animada.
- Discord: `https://discord.gg/Eux3UUKvXg`.

## Herramientas nuevas de esta versión

- Orbdiff/Others: VMAware, ConsoleHostHistory y Journal Deleted Detector.
- Scripts: Lilith Script, Lilith DoomsDay Finder y Habibi Mod Analyzer.
- Scripts: Macro Catcher se ejecuta mediante CMD con permisos de administrador.
- Others Tools: MacroScanner se descarga y ejecuta como administrador; VirusTotal abre su página de carga en el navegador.
- Zeedoonvm1 Doomsday Detector ahora es Real Doomsday Detector y usa el scanner actualizado.
- Service Enabler ahora aparece como Lilith Services Enabler.
- .NET 10.0 y .NET 9.0 instalan los Desktop Runtime x64 indicados.

Los ejecutables se descargan en `tools/<categoria>/`, se validan como archivos PE y se abren automáticamente. Cuando existe un SHA-256 configurado también se verifica antes de ejecutar. Los scripts indicados se abren en CMD con los permisos de administrador heredados de la aplicación.

## Ejecutar desde Python

1. Instala Python 3.12 de 64 bits.
2. Crea un entorno con `py -3.12 -m venv .venv`.
3. Actívalo con `.venv\Scripts\activate`.
4. Ejecuta `python -m pip install -r requirements.txt`.
5. Ejecuta `python main.py`.


El instalador de dependencias no utiliza la caché global de `pip`, evitando
errores de permisos causados por ruedas bloqueadas o creadas por otro usuario.

El compilador usa un entorno separado `.build-venv-312`, sin reutilizar ni borrar
los entornos anteriores de Python 3.13/3.14. Comprueba Tcl/Tk antes de instalar dependencias
y pasa sus rutas reales a Nuitka. Si falta Tcl/Tk, repara la instalación de Python
3.12 activando ese componente. No se han cambiado la interfaz ni las herramientas.

La compilación usa Nuitka en modo onefile: convierte los módulos a C, activa LTO,
elimina docstrings y asserts y solicita permisos de administrador mediante UAC.
Esto dificulta la extracción casual del catálogo y de la lógica, aunque ningún
secreto guardado dentro de un ejecutable puede protegerse de forma absoluta.
El icono del ejecutable, la ventana y la barra de tareas se toma de
`assets/PsicoseadoSSTool.ico`.

La cabecera permanece completamente oculta durante la introducción y aparece
directamente al terminar. Las descargas con tamaño conocido enseñan una barra
horizontal y el porcentaje real de 0 a 100 % dentro de la notificación inferior;
los servidores sin `Content-Length` mantienen 0 % durante la transferencia y
terminan en 100 %. Las tarjetas no muestran el progreso de descarga.

## Verificación

Ejecuta `python -m unittest discover -s tests -v`. Las pruebas cubren el inventario, orden solicitado, enlaces de los Desktop Runtime, Event Viewer, cooldown, animaciones, reutilización de tarjetas, minimizado y enlaces externos.

## Open source

El código original se publica bajo la licencia [MIT](LICENSE). Consulta
[CONTRIBUTING.md](CONTRIBUTING.md) antes de enviar cambios, [SECURITY.md](SECURITY.md)
para reportes de seguridad y [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
para información sobre herramientas externas.

Los ejecutables y scripts descargados por la aplicación no forman parte de este
repositorio y conservan las licencias de sus respectivos autores.
