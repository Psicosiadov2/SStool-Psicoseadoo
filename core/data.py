"""
Modelo de datos: categorias (pestanas) y herramientas de cada una.

Cada herramienta es un dict:
    {
        "name": "Nombre visible",
        "desc": "Descripcion corta",
        "path": "NombreDelEjecutable.exe"  -> se busca en tools/<categoria_id>/
        "url":  "https://..."             -> descarga estable del ejecutable/ZIP
        "sha256": "..."                   -> hash esperado del archivo descargado
        "archive": True                    -> indica que el enlace contiene un ZIP
        "installed_sha256": "..."         -> hash del EXE extraido del ZIP
        "runner": "powershell"             -> abre un .ps1 en una consola nueva
        "cmd_command": "powershell ..."     -> ejecuta el comando exacto dentro de CMD
        "embedded_script": "..."           -> script incluido dentro de la app
        "mediafire_page": "https://..."    -> pagina estable para resolver MediaFire
    }

Deja "path" y "url" en None hasta que tengas la herramienta real; el launcher
avisara en pantalla que falta configurarla en vez de fallar en silencio.

Para agregar herramientas a una categoria vacia solo agrega dicts nuevos a su
lista "tools".
"""

CATEGORIES = [
    {
        "id": "orbdiff",
        "label": "Orbdiff/Others",
        "icon": "\u25CE",  # ◎
        "header": None,
        "tools": [
            {
                "name": "PrefetchView++",
                "desc": "Parses prefetch extracting file info",
                "path": "PrefetchView++.exe",
                "url": "https://github.com/Orbdiff/PrefetchView/releases/download/v1.6.8/pv%2B%2B.exe",
                "sha256": "4a759585a6f37f96f6aefa72db7f2ad79d607d682523e6f30ea259cbeb42c567",
            },
            {
                "name": "BAMReveal",
                "desc": "Parses BAM forensic artefact",
                "path": "BAMReveal.exe",
                "url": "https://github.com/Orbdiff/BAMReveal/releases/download/v1.3.1/BAMReveal.exe",
                "sha256": "4857fabf9c7ab1e44c59af5767f39b17686d8aae1098372c454e0c0ffa4550ac",
            },
            {
                "name": "JournalParser",
                "desc": "Parses NTFS USNJournal entries",
                "path": "JournalParser.exe",
                "url": "https://github.com/Orbdiff/JournalParser/releases/download/v1.2/JournalParser.exe",
                "sha256": "8195c6237c41e0deb6783e151f0ec37c93830b7c730e2c98d67b1c0c1e3b7657",
            },
            {
                "name": "Fileless",
                "desc": "Detect fileless via eventlog + memdump",
                "path": "Fileless.exe",
                "url": "https://github.com/Orbdiff/Fileless/releases/download/v1.3/fileless.exe",
                "sha256": "245929075877337ec4565160ea68a2afa3e5f7732f0087ddeffef43dc43afad4",
            },
            {
                "name": "ConsoleHostHistory",
                "desc": "The already integrated console host history of PowerShell",
                "cmd_command": (
                    "powershell -NoLogo -NoProfile -Command "
                    "\"Get-Content (Get-PSReadLineOption).HistorySavePath\""
                ),
            },
            {
                "name": "Eventvwr",
                "desc": "Windows Event Viewer used to view system, application, security, and error logs for troubleshooting and diagnostics.",
                "native_command": "eventvwr.exe",
            },
            {
                "name": "JARParser",
                "desc": "Parses JAR prefetch, DcomLaunch strings, etc",
                "path": "JARParser.exe",
                "url": "https://github.com/Orbdiff/JARParser/releases/download/v1.2/JARParser.exe",
                "sha256": "68cd2b0427f9fb48f68141917f2b1eac6824f7f8b59ccea708052246437da736",
            },
            {
                "name": "PFTrace",
                "desc": "Rundll32/Regsvr32 prefetch analysis",
                "path": "PFTrace.exe",
                "url": "https://github.com/Orbdiff/PFTrace/releases/download/v1.0.1/PFTrace.exe",
                "sha256": "c0d8a21406d6c7cb1a5a50f288af70d833a7c065fa0528819d322c9efec02efc",
            },
            {
                "name": "InjGen",
                "desc": "Detects JNI/JVMTI memory injections",
                "path": "InjGen.exe",
                "url": "https://github.com/Orbdiff/InjGen/releases/download/fork/InjGen.exe",
                "sha256": "226ebb238f0bbce73461ed28820d2f8eee55f8bbd5aefaa83dc2cff641e818c0",
            },
            {
                "name": "DPS-Analyzer",
                "desc": "Analyzes DPS memory",
                "path": "DPS-Analyzer.exe",
                "url": "https://github.com/Orbdiff/DPS-Analyzer/releases/download/v1.1/dpsanalyzer.exe",
                "sha256": "20128c5dd2b9209873b5a631d3883507853ab0e6fba362b89b93870735ad3285",
            },
            {
                "name": "USBDetector",
                "desc": "Detects USB device history",
                "path": "USBDetector.exe",
                "url": "https://github.com/Orbdiff/USBDetector/releases/download/v1.1/USBDetector.exe",
                "sha256": "caa6440b90c49163127d308594fff1c0cb26c26f8d0f43ab6e5a74e888dd971e",
            },
            {
                "name": "UserAssistView",
                "desc": "Parser UserAssist artifact",
                "path": "UserAssistView.exe",
                "url": "https://github.com/Orbdiff/UserAssistView/releases/download/v1.0/UserAssistView.exe",
                "sha256": "65eed4536f1aa21fedd3e92ba32b9ef3682fcaf065d5c61e1239c6b7bf974c33",
            },
            {
                "name": "StringsParser",
                "desc": "Strings + YARA + signatures scanner",
                "path": "StringsParser.exe",
                "url": "https://github.com/Orbdiff/StringsParser/releases/download/v1.2.1b/stringsparser.1.2.1b.exe",
                "sha256": "0453ba458b362ccfcfa502cef1c20d1ffb73c65cc0dfed1bba6b125d33e54fd2",
            },
            {
                "name": "USB Deview",
                "desc": "Manages USB devices.",
                "path": "USBDeview.exe",
                "url": "https://www.nirsoft.net/utils/usbdeview.zip",
                "sha256": "30e2f5103420630650d3bba3f5d28a828e664c414ba3baa2a979bc19b2bf12f6",
                "archive": True,
                "installed_sha256": "706e0f5e6cd53a5c43394f09b7bfa51d5c6783c098bdf1225102c8eecf58d3ed",
            },
            {
                "name": "BrowserDownloadsView",
                "desc": "View browser download history",
                "path": "BrowserDownloadsView.exe",
                "url": "https://www.nirsoft.net/utils/browserdownloadsview.zip",
                "sha256": "60e95026983e128a81f7c7ed11fe7e94373ce4604216fd879f7d340cf8844d3a",
                "archive": True,
                "installed_sha256": "47cab171cc417e98b1189a38dfe22bba8610f19bd5b0fb35ede702c70a63e476",
            },
            {
                "name": "P1AE Scanner",
                "desc": "A screenshare tool that scans the javaw.exe processes memory for known and unknown cheat strings",
                "path": "P1AE.Javaw.exe",
                "url": "https://github.com/p1aegg/javaw/releases/download/v1.12/P1AE.Javaw.exe",
                "sha256": "f20057ba35dd1cbb2750e43b728fdb108a1fd3d93aed4ddff9a7e05c0f26fb76",
            },
            {
                "name": "Siege",
                "desc": "A Windows-based automatic screenshare tool, mostly intended for Minecraft.",
                "path": "Siege.exe",
                "url": "https://github.com/praiselily/Siege/releases/download/Scanner/Siege.exe",
                "sha256": "633bf91a396ece923f42f3bd3ef523c962b99efa5af5b587dbdd6d3c2499bd22",
                "run_as_admin": True,
            },
            {
                "name": "RedLotus Mod Analyzer",
                "desc": "Automatically detects the running javaw.exe process and scans the mods currently loaded in memory.",
                "path": "RedLotusModAnalyzer.exe",
                "url": "https://github.com/ItzIceHere/RedLotus-Mod-Analyzer/releases/download/RL/RedLotusModAnalyzer.exe",
                "sha256": "4b7af53b5407595abb8969e6bfe1dd6eba85553e541a26697ae1230a4561e853",
            },
            {
                "name": "VMAware",
                "desc": "Virtual machine detector.",
                "path": "vmaware32.exe",
                "url": "https://github.com/NotRequiem/VMAware/releases/download/v2.8.2/vmaware32.exe",
                "sha256": "131a13eac73b8d34d36ef84c2b8192fef0bc1075b58ba3182e314685eb9769df",
                "run_as_admin": True,
            },
            {
                "name": "Journal Deleted Detector",
                "desc": "Detects deleted Journal",
                "path": "JournalDeletedDetector.ps1",
                "runner": "powershell",
                "embedded_script": (
                    "Write-Host 'Time Changed Scanning...' -ForegroundColor Yellow\n"
                    "try {\n"
                    "  Get-EventLog -LogName Security -InstanceId 4616 -ErrorAction Stop | Select -ExpandProperty TimeGenerated\n"
                    "} catch {\n"
                    "  Write-Host 'Nothing found'\n"
                    "}\n"
                    "Write-Host ''\n"
                    "Write-Host 'Journal Deleted logs scanning...' -ForegroundColor Yellow\n"
                    "Write-Host ''\n"
                    "try {\n"
                    "    Get-WinEvent -FilterHashtable @{LogName='Application'; Id=3079} -ErrorAction Stop | Select-Object -ExpandProperty TimeCreated\n"
                    "} catch {\n"
                    "    Write-Host 'Nothing found...'\n"
                    "}\n"
                ),
            },
        ],
    },
    {
        "id": "spokwn",
        "label": "MeowTonynoh",
        "icon": "\u2630",  # ☰
        "header": None,
        "tools": [
            {
                "name": "Meow Client Fucker",
                "desc": (
                    "Forensic analysis tool for Minecraft screenshare anticheat. "
                    "Detects cheat clients through RAM memory scanning (Javaw) and "
                    "DNS cache analysis, with generic module detection that flags "
                    "suspicious behavior independently from the client."
                ),
                "path": "MeowClientFucker.exe",
                "url": "https://github.com/MeowTonynoh/MeowClientFucker/releases/download/V1.1/MeowClientFucker.exe",
                "sha256": "4afce4998dc5a336a6c8a503869bf9331ad2dffae125f10f7d4debfd3761bd73",
                "height": 150,
            },
            {
                "name": "Meow Resolver",
                "desc": (
                    "A Windows forensic tool that detects and removes common bypass "
                    "techniques, restrictions, and anti-forensic manipulations from "
                    "the system registry, event logs, and file system."
                ),
                "path": "MeowResolver.exe",
                "url": "https://github.com/MeowTonynoh/MeowResolver/releases/download/v.1.1/MeowResolver.exe",
                "sha256": "cfbb52658b64c4b520e9d3d271e4622f464febf295043a0127e34c07c0fec7e1",
                "height": 130,
            },
            {
                "name": "Meow Imports Checker",
                "desc": (
                    "Forensic analysis tool. Scans files for cheat client signatures, "
                    "suspicious behavioral patterns, Strings, PE imports, obfuscation "
                    "artifacts, and injection techniques — with integrated VirusTotal "
                    "verification."
                ),
                "path": "MeowImportsChecker.exe",
                "url": "https://github.com/MeowTonynoh/MeowImportsChecker/releases/download/MeowImportsChecker/MeowImportsChecker.exe",
                "sha256": "33b5ab7cba9111f8b43c07c9b777010c30c7e14de46d275671a486ef9606a1a3",
                "height": 145,
            },
            {
                "name": "Meow Mod Analyzer",
                "desc": "CMD script to analyze Minecraft mods and identify potential cheat clients.",
                "path": "MeowModAnalyzer.ps1",
                "url": "https://raw.githubusercontent.com/MeowTonynoh/MeowModAnalyzer/5221bfd6ae78b9dd1d3ce1057ee46cc83da3deff/MeowModAnalyzer.ps1",
                "sha256": "86e85fe808242e784ab26236e70ac25baa67adfb1f01dc838afb6e7da43c2bfd",
                "runner": "powershell",
                "cmd_command": (
                    "powershell -ExecutionPolicy Bypass -Command "
                    "\"Invoke-Expression (Invoke-RestMethod "
                    "'https://raw.githubusercontent.com/MeowTonynoh/"
                    "MeowModAnalyzer/main/MeowModAnalyzer.ps1')\""
                ),
                "height": 110,
            },
        ],
    },
    {
        "id": "redlotus",
        "label": "Spokwn",
        "icon": "\u2726",  # ✦
        "header": None,
        "tools": [
            {
                "name": "JournalTrace",
                "desc": "Parses NTFS journal entries",
                "path": "JournalTrace.exe",
                "url": "https://github.com/ponei/JournalTrace/releases/download/1.0/JournalTrace.exe",
                "sha256": "46873781a5c80ea676f0ed8024b31423f22918d9f4723aba49b22c8e597ec0e6",
            },
            {
                "name": "KernelDumpTool",
                "desc": "Reads LiveKernel dumps, custom keywords",
                "path": "KernelLiveDumpTool.exe",
                "url": "https://github.com/spokwn/KernelLiveDumpTool/releases/download/v1.1/KernelLiveDumpTool.exe",
                "sha256": "b28ea771595d1a020ca04af2bed7008b9e6a65bb23ac9fe385aaa3341b21af9e",
            },
        ],
    },
    {
        "id": "scripts",
        "label": "Scripts",
        "icon": "\u25A4",  # ▤
        "header": None,
        "tools": [
            {
                "name": "AguaScript",
                "desc": "Detects multiple threats against a Scheduled Task on a user's PC using a PowerShell script.",
                "path": "AguaScript.ps1",
                "url": "https://raw.githubusercontent.com/AguaConGas17/Powershells/86e2634d54715d9275f1f819351d1ed64bbb5790/aguascript.ps1",
                "sha256": "e0df4a0ff0dd8f992ccc0f4401a3fa1550b6b19739517ee6a48522fa71e3d685",
                "runner": "powershell",
            },
            {
                "name": "Lilith Script",
                "desc": "Detects multiple threats against a SS on a users PC",
                "cmd_command": "powershell -ExecutionPolicy Bypass -Command \"iex (irm 'https://raw.githubusercontent.com/inkenal/rbw-SS-ps/refs/heads/main/Services.ps1')\"",
            },
            {
                "name": "Lilith Services Enabler",
                "desc": (
                    "Detects enabled and disabled services including their start up time "
                    "and how they are running letting us enable them or disable them."
                ),
                "path": "Service-Enabler.ps1",
                "url": "https://raw.githubusercontent.com/praiselily/lilith-ps/89a9f9029efbb204665c0dae3a2e40d8d4d6ea81/Service-Enabler.ps1",
                "sha256": "359ff89de147527b2326af558f04b4cd9170e16bb2055354e2ecd7e74d36d236",
                "runner": "powershell",
            },
            {
                "name": "Real Doomsday Detector",
                "desc": "Detects Doomsday Client on the user's PC.",
                "cmd_command": (
                    "powershell -Command \"Invoke-Expression (Invoke-RestMethod "
                    "'https://raw.githubusercontent.com/reala1-staff/"
                    "DoomsdayScannerModified/refs/heads/main/Doomsday-scannerv3.ps1')\""
                ),
            },
            {
                "name": "Lilith DoomsDay Finder",
                "desc": "Fast runable script to detect DoomsDay client on a users PC",
                "cmd_command": "powershell -Command \"Set-ExecutionPolicy Bypass -Scope Process; Invoke-Expression (Invoke-RestMethod 'https://raw.githubusercontent.com/praiselily/lilith-ps/refs/heads/main/DoomsdayFinder.ps1')\"",
            },
            {
                "name": "VPN Detector",
                "desc": "Detects active VPN/Proxy active on the users PC.",
                "path": "VPNDetector.ps1",
                "url": None,
                "runner": "powershell",
                "embedded_script": (
                    "$ErrorActionPreference = 'Stop'\n"
                    "$ip = (Invoke-WebRequest -UseBasicParsing 'https://ifconfig.me/ip').Content.Trim()\n"
                    "$result = Invoke-RestMethod -Uri \"https://proxycheck.io/v2/${ip}?vpn=1&asn=1\"\n"
                    "$outputPath = Join-Path $env:TEMP 'proxy.json'\n"
                    "$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $outputPath -Encoding UTF8\n"
                    "$isProxy = $false\n"
                    "if ($result.PSObject.Properties.Name -contains $ip) {\n"
                    "    $isProxy = ($result.$ip.proxy -eq 'yes')\n"
                    "}\n"
                    "Write-Host \"IP consultada: $ip\"\n"
                    "Write-Host \"VPN/Proxy detectado: $isProxy\"\n"
                    "Write-Host \"Resultado guardado en: $outputPath\"\n"
                ),
            },
            {
                "name": "RecordingKiller",
                "desc": "Kill recording processes (or atleast try to)",
                "path": "RecordingKiller.ps1",
                "url": "https://raw.githubusercontent.com/Orbdiff/powershell/7f962e60c818cfb049b46a9f86907a36b5e272df/kill-screen-processes.ps1",
                "sha256": "e20e76defc950c39971d3e3a796b73173a9c3bebb49dcf94172abb6eab54517a",
                "runner": "powershell",
            },
            {
                "name": "Habibi Mod Analyzer",
                "desc": "Revisará los mods de la carpeta que le indique y te dirá si son mods verificados o no. También revisará strings sospechosas:",
                "cmd_command": "powershell -command \"irm 'https://raw.githubusercontent.com/HadronCollision/PowershellScripts/refs/heads/main/HabibiModAnalyzer.ps1' | iex\"",
            },
        ],
    },
    {
        "id": "nirsoft",
        "label": "Others Tools",
        "icon": "\u25A3",  # ▣
        "header": None,
        "tools": [
            {
                "name": "Jarabel",
                "desc": "Locate .jar files with detailed checks",
                "path": "Jarabel.exe",
                "url": "https://download848.mediafire.com/qxg9ql6sskpgZo9yrk-ifZ1oxSqcbBQNQ7lWHtfeePwr3AtVGhxknuNag19bNAPCaxuKSdojvhYZt6aP5nKf0vZv927Sd3EDQk1vEqSEFkWJh8UylEP6U4wwhX_IC-F3OVPEIdOEMlOX5NkdkGeN2K6CfFP3SXUVNeAnr-ZbPGew/3ejw2o0un4ggjr3/Jarabel.exe",
                "mediafire_page": "https://www.mediafire.com/file/3ejw2o0un4ggjr3/Jarabel.exe/file",
            },
            {
                "name": "Luyten",
                "desc": "Luyten Java decompiler",
                "path": "Luyten.exe",
                "url": "https://download1584.mediafire.com/h2ls0s0gw1cgLFlUsitbkh9Sjv_Q13O51qiFNc7-usyE29WMhqU4Ijz1kk9MCkfXkb0DBGjNBNBabmJwzYwlPUIG_uBmXueIruds3TuVVQUjweh0GZxYcJfdXS9wmWkXADDDkgyEEjJ1kGKG51uqIv7T6zVO2zOZPfRcFewmUo0y/k1r843zp4kuwc6f/Luyten.exe",
                "mediafire_page": "https://www.mediafire.com/file/k1r843zp4kuwc6f/Luyten.exe/file",
            },
            {
                "name": "Everything",
                "desc": "Everything search engine",
                "path": "Everything-1.4.1.1032.x86-Setup.exe",
                "url": "https://www.voidtools.com/Everything-1.4.1.1032.x86-Setup.exe",
                "sha256": "781a31b440045219752a1bb40fbd204b1d96964d4bf56af01b18e3d549b037aa",
            },
            {
                "name": "Sytem Informer",
                "desc": (
                    "A highly powerful, multipurpose tool that helps you monitor system "
                    "resources, debug software, and detect malware.\n\n"
                    "It makes accessing services and processes very easy, allowing us to "
                    "dump and analyze them to look for cheats. The most commonly used "
                    "services are:"
                ),
                "path": "systeminformer-build-canary-setup.exe",
                "url": "https://github.com/winsiderss/si-builds/releases/download/4.0.26255.346/systeminformer-build-canary-setup.exe",
                "sha256": "094eeed9bca1857902f093d62fcff7f3ed11af87791b4d363724fb4955fbbbeb",
            },
        ],
    },
    {
        "id": "dependencies",
        "label": "Dependencies",
        "icon": "",
        "header": None,
        "tools": [
            {
                "name": ".NET 10.0",
                "desc": "The .NET Desktop Runtime enables you to run existing Windows desktop applications.",
                "path": "windowsdesktop-runtime-10.0.5-win-x64.exe",
                "url": "https://builds.dotnet.microsoft.com/dotnet/WindowsDesktop/10.0.5/windowsdesktop-runtime-10.0.5-win-x64.exe?utm_source=chatgpt.com",
            },
            {
                "name": ".NET 9.0",
                "desc": "The .NET Desktop Runtime enables you to run existing Windows desktop applications.",
                "path": "windowsdesktop-runtime-9.0.14-win-x64.exe",
                "url": "https://builds.dotnet.microsoft.com/dotnet/WindowsDesktop/9.0.14/windowsdesktop-runtime-9.0.14-win-x64.exe?utm_source=chatgpt.com",
            },
            {
                "name": "Microsoft Visual C++ v14",
                "desc": "runtime library and compiler toolset used by Microsoft to build, run, and execute C++ applications across Visual Studio versions",
                "path": "vc_redist.x64.exe",
                "url": "https://aka.ms/vc14/vc_redist.x64.exe",
            },
            {
                "name": "Java",
                "desc": "Designed to run, develop, and manage robust, object-oriented applications on Microsoft Windows environments.",
                "path": "JavaSetup.exe",
                "url": "https://javadl.oracle.com/webapps/download/AutoDL?BundleId=253606_2fde65a2208f40a5b5f4c844b0dff092",
            },
        ],
    },
]


def get_category(category_id):
    for cat in CATEGORIES:
        if cat["id"] == category_id:
            return cat
    return None
