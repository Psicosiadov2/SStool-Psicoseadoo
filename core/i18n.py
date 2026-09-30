"""Small in-memory translation layer. English intentionally resets every launch."""

DEFAULT_LANGUAGE = "en"

UI = {
    "en": {
        "contact": "Contact: Psicoseado",
        "empty": "This category does not contain tools yet.",
        "available": "Available in {seconds:.1f}s",
        "opening": "Opening...",
        "preparing": "Preparing {name}...",
        "already_running": "This operation is already in progress.",
        "unexpected": "The operation failed unexpectedly:\n{error}",
        "downloading": "Downloading and verifying {name}...",
    },
    "es": {
        "contact": "Contacto: Psicoseado",
        "empty": "Esta categoría todavía no contiene herramientas.",
        "available": "Disponible en {seconds:.1f}s",
        "opening": "Abriendo...",
        "preparing": "Preparando {name}...",
        "already_running": "Esta operación ya está en progreso.",
        "unexpected": "La operación falló de forma inesperada:\n{error}",
        "downloading": "Descargando y verificando {name}...",
    },
}

CATEGORY_ES = {
    "orbdiff": "Orbdiff/Otros",
    "spokwn": "MeowTonynoh",
    "redlotus": "Spokwn",
    "scripts": "Scripts",
    "nirsoft": "Otras herramientas",
    "dependencies": "Dependencias",
}

TOOL_DESC_ES = {
    "PrefetchView++": "Analiza Prefetch y extrae información de archivos",
    "BAMReveal": "Analiza el artefacto forense BAM",
    "JournalParser": "Analiza entradas del USN Journal de NTFS",
    "Fileless": "Detecta actividad fileless mediante registros de eventos y volcados de memoria",
    "ConsoleHostHistory": "Historial integrado de la consola de PowerShell",
    "Eventvwr": "Visor de eventos de Windows para consultar registros del sistema, aplicaciones, seguridad y errores.",
    "JARParser": "Analiza Prefetch de JAR, cadenas de DcomLaunch y más",
    "PFTrace": "Análisis Prefetch de Rundll32 y Regsvr32",
    "InjGen": "Detecta inyecciones de memoria JNI/JVMTI",
    "DPS-Analyzer": "Analiza la memoria de DPS",
    "USBDetector": "Detecta el historial de dispositivos USB",
    "UserAssistView": "Analiza el artefacto UserAssist",
    "StringsParser": "Escáner de cadenas, YARA y firmas",
    "USB Deview": "Administra dispositivos USB.",
    "BrowserDownloadsView": "Muestra el historial de descargas de navegadores",
    "P1AE Scanner": "Herramienta de screenshare que analiza la memoria de javaw.exe en busca de cadenas de cheats conocidas y desconocidas",
    "Siege": "Herramienta automática de screenshare para Windows, orientada principalmente a Minecraft.",
    "RedLotus Mod Analyzer": "Detecta automáticamente javaw.exe y analiza los mods cargados actualmente en memoria.",
    "VMAware": "Detector de máquinas virtuales.",
    "Journal Deleted Detector": "Detecta la eliminación del Journal",
    "Meow Client Fucker": "Herramienta forense para screenshares de Minecraft. Detecta clientes cheat mediante RAM de Javaw, caché DNS y módulos sospechosos.",
    "Meow Resolver": "Herramienta forense de Windows que detecta y elimina bypasses, restricciones y manipulaciones antiforenses.",
    "Meow Imports Checker": "Analiza firmas de clientes cheat, patrones sospechosos, cadenas, imports PE, ofuscación e inyección, con VirusTotal.",
    "Meow Mod Analyzer": "Script CMD para analizar mods de Minecraft e identificar posibles clientes cheat.",
    "JournalTrace": "Analiza entradas del Journal de NTFS",
    "KernelDumpTool": "Lee volcados LiveKernel con palabras clave personalizadas",
    "AguaScript": "Detecta múltiples amenazas contra tareas programadas mediante PowerShell.",
    "Lilith Script": "Detecta múltiples amenazas contra una screenshare en el PC del usuario",
    "Lilith Services Enabler": "Detecta servicios habilitados y deshabilitados, su inicio y ejecución, y permite administrarlos.",
    "Real Doomsday Detector": "Detecta el cliente Doomsday en el PC del usuario.",
    "Lilith DoomsDay Finder": "Script rápido para detectar el cliente DoomsDay en un PC",
    "VPN Detector": "Detecta VPN o proxy activos en el PC del usuario.",
    "RecordingKiller": "Intenta detener procesos de grabación",
    "Habibi Mod Analyzer": "Revisa mods y cadenas sospechosas e indica si los mods están verificados.",
    "Jarabel": "Localiza archivos .jar y realiza comprobaciones detalladas",
    "Luyten": "Descompilador de Java Luyten",
    "Everything": "Motor de búsqueda Everything",
    "Sytem Informer": "Herramienta multipropósito para monitorizar recursos, depurar software, detectar malware y analizar servicios y procesos.",
    ".NET 10.0": "El runtime de escritorio .NET permite ejecutar aplicaciones de escritorio de Windows existentes.",
    ".NET 9.0": "El runtime de escritorio .NET permite ejecutar aplicaciones de escritorio de Windows existentes.",
    "Microsoft Visual C++ v14": "Biblioteca runtime y herramientas de compilación para crear y ejecutar aplicaciones C++.",
    "Java": "Diseñado para ejecutar, desarrollar y administrar aplicaciones robustas orientadas a objetos en Windows.",
}


def tr(key, language=DEFAULT_LANGUAGE, **values):
    language = language if language in UI else DEFAULT_LANGUAGE
    return UI[language].get(key, UI[DEFAULT_LANGUAGE].get(key, key)).format(**values)


def category_label(category, language=DEFAULT_LANGUAGE):
    if language == "es":
        return CATEGORY_ES.get(category["id"], category["label"])
    return category["label"]


def tool_description(tool, language=DEFAULT_LANGUAGE):
    if language == "es":
        return TOOL_DESC_ES.get(tool["name"], tool["desc"])
    return tool["desc"]
