# Interfaz Glass del HTML adjunto

La interfaz principal ahora utiliza el fondo incrustado y CSS del archivo
RF-Forensics-Glass (5).html, renderizados por Edge WebView2 mediante pywebview.
Tema negro/blanco y fondo del nuevo HTML. Contact, EN/ES, GitHub, Discord y
búsqueda se muestran encima de las categorías. La intro conserva assets/Intro.png:
Napoleón y el texto «Tal vez el bypass siempre fue inevitable», sin recortes.
No es una imagen ni una simulación en Tkinter. El motor de descargas y comandos
en core/launcher.py y el catálogo de core/data.py no se modificaron.

- 44 herramientas, seis categorías, sin Siege ni iconos en tarjetas.
- EN predeterminado, selector ES; descripciones originales del catálogo.
- Búsqueda global, cooldown visible de cinco segundos y bloqueo mientras trabaja.
- Notificación con progreso horizontal real; indeterminado si no hay tamaño total.
- Minimizar, maximizar/restaurar, cerrar; F11 alterna pantalla completa.
- Intro de tres segundos, cabecera oculta durante ella.

## Ejecutar y compilar en Windows 10/11

Instala Python 3.12 x64 y Microsoft Edge WebView2 Runtime si falta.
Ejecuta `py -3.12 -m pip install -r requirements.txt`, luego `py -3.12 main.py`.
Para compilar, abre BUILD_GLASS.bat (BUILD_EXE.bat también lo llama).
El resultado es dist/PsicoseadoSSTool.exe. La compilación pide UAC normalmente;
no evita protecciones de Windows. No se han ejecutado las herramientas de terceros
durante la verificación. La compilación y la integración nativa WebView2 requieren
validación en Windows; no se afirma que se hayan probado en este entorno Linux.

`preview.html` es la misma interfaz y catálogo exportados para inspección en navegador.
Allí no descarga ni ejecuta nada: esas acciones solo están disponibles dentro de la app.
La carpeta ui conserva módulos Tk antiguos únicamente como referencia y para las pruebas
anteriores; main.py ya no los utiliza.
