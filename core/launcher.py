"""Descarga, verifica y ejecuta las herramientas conectadas a cada tarjeta."""

import hashlib
import hmac
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from html.parser import HTMLParser

from core.config import TOOLS_ROOT


DOWNLOAD_TIMEOUT = 30
DOWNLOAD_MAX_SECONDS = 600
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
USER_AGENT = "PsicoseadoSSTool/1.0 (Windows tool launcher)"
MAX_SCRIPT_BYTES = 8 * 1024 * 1024
MAX_SOURCE_PAGE_BYTES = 2 * 1024 * 1024
INSTALL_MARKER_SUFFIX = ".psicoseado-sstool.json"
INSTALL_MARKER_SCHEMA = 1
ZIMMERMAN_PRIMARY = "https://download.ericzimmermanstools.com/"
ZIMMERMAN_MIRROR = "https://f001.backblazeb2.com/file/EricZimmermanTools/"
ZIMMERMAN_INDEX_PAGES = (
    "https://tools.ericzimmermanstools.com",
    "https://ericzimmerman.github.io/index.md",
    "https://raw.githubusercontent.com/EricZimmerman/ericzimmerman.github.io/master/index.md",
)
ZIMMERMAN_HOSTS = ("download.ericzimmermanstools.com", "f001.backblazeb2.com")


class ToolDownloadError(RuntimeError):
    """Error controlado durante la descarga o validacion de una herramienta."""


class _MediaFireDownloadParser(HTMLParser):
    """Extrae el enlace oficial del boton de descarga de una pagina MediaFire."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.download_url = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a" or self.download_url:
            return
        attributes = dict(attrs)
        if attributes.get("id") == "downloadButton" and attributes.get("href"):
            self.download_url = attributes["href"]


def _base_dir():
    """Carpeta persistente junto al script o al ejecutable compilado."""
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def downloads_directory():
    """Devuelve la carpeta Descargas del usuario en Windows y otros sistemas."""
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        return os.path.join(user_profile, "Downloads")
    return os.path.join(os.path.expanduser("~"), "Downloads")


def tools_root_directory():
    return os.path.join(downloads_directory(), TOOLS_ROOT)


def ensure_tools_root():
    root = tools_root_directory()
    os.makedirs(root, exist_ok=True)
    return root


def resolve_tool_path(category_id, tool):
    """Ruta absoluta esperada del ejecutable de una herramienta."""
    path = tool.get("path")
    if not path:
        return None
    return os.path.join(tools_root_directory(), category_id, path)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _embedded_sha256(tool):
    script = tool.get("embedded_script")
    if script is None:
        return None
    return hashlib.sha256(script.encode("utf-8")).hexdigest()


def _installed_sha256(tool):
    embedded_hash = _embedded_sha256(tool)
    if embedded_hash:
        return embedded_hash
    if tool.get("archive"):
        return tool.get("installed_sha256")
    return tool.get("sha256")


def _install_source(tool):
    embedded_hash = _embedded_sha256(tool)
    if embedded_hash:
        return f"embedded:{embedded_hash}"
    return tool.get("mediafire_page") or tool.get("url") or ""


def _install_marker_path(path):
    return f"{path}{INSTALL_MARKER_SUFFIX}"


def _is_valid_install(path, tool):
    if tool.get("always_download"):
        return False
    if not path or not os.path.isfile(path):
        return False

    # Un archivo local solo se reutiliza si este launcher dejo su manifiesto de
    # procedencia al completar una descarga anterior. La mera coincidencia del
    # nombre o incluso del hash publico no convierte un archivo preexistente en
    # una instalacion propiedad de PsicoseadoSSTool.
    try:
        with open(_install_marker_path(path), "r", encoding="utf-8") as marker_file:
            marker = json.load(marker_file)
        if marker.get("schema") != INSTALL_MARKER_SCHEMA:
            return False
        if marker.get("tool") != tool.get("name"):
            return False
        if marker.get("source") != _install_source(tool):
            return False
        marker_hash = marker.get("sha256", "")
        actual_hash = _sha256(path)
    except (AttributeError, OSError, TypeError, ValueError):
        return False

    if not marker_hash or not hmac.compare_digest(
        actual_hash.lower(), str(marker_hash).lower()
    ):
        return False

    expected = _installed_sha256(tool)
    return not expected or hmac.compare_digest(actual_hash.lower(), expected.lower())


def _validate_executable(path):
    if not os.path.isfile(path):
        raise ToolDownloadError("el ejecutable esperado no se encontro despues de la descarga")
    with open(path, "rb") as file_handle:
        if file_handle.read(2) != b"MZ":
            raise ToolDownloadError("el archivo descargado no es un ejecutable valido de Windows")


def _validate_powershell_script(path):
    if not os.path.isfile(path):
        raise ToolDownloadError("el script esperado no se encontro despues de la descarga")
    if os.path.getsize(path) > MAX_SCRIPT_BYTES:
        raise ToolDownloadError("el script supera el limite de seguridad de 8 MB")
    with open(path, "rb") as file_handle:
        raw_script = file_handle.read()
    if b"\x00" in raw_script:
        raise ToolDownloadError("el script descargado contiene datos binarios inesperados")
    try:
        raw_script.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ToolDownloadError("el script descargado no tiene codificacion UTF-8 valida") from exc


def _validate_payload(path, tool):
    if tool.get("runner") == "powershell":
        _validate_powershell_script(path)
    else:
        _validate_executable(path)


def _write_install_marker(path, tool):
    """Registra que PsicoseadoSSTool descargo y valido esta instalacion."""
    marker_path = _install_marker_path(path)
    temp_path = f"{marker_path}.tmp"
    marker = {
        "schema": INSTALL_MARKER_SCHEMA,
        "tool": tool.get("name", ""),
        "source": _install_source(tool),
        "sha256": _sha256(path),
    }
    try:
        with open(temp_path, "w", encoding="utf-8", newline="\n") as marker_file:
            json.dump(marker, marker_file, ensure_ascii=False, sort_keys=True)
            marker_file.write("\n")
        os.replace(temp_path, marker_path)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def _mark_as_downloaded(path):
    """Conserva las protecciones de Windows (Mark of the Web) cuando sea posible."""
    if not sys.platform.startswith("win"):
        return
    try:
        with open(f"{path}:Zone.Identifier", "w", encoding="ascii") as zone_file:
            zone_file.write("[ZoneTransfer]\nZoneId=3\n")
    except OSError:
        # Algunos sistemas de archivos no admiten alternate data streams.
        pass


def _download_to_temp(url, target_dir, expected_sha256=None, on_progress=None):
    os.makedirs(target_dir, exist_ok=True)
    file_descriptor, temp_path = tempfile.mkstemp(prefix=".sstool-download-", dir=target_dir)
    os.close(file_descriptor)

    digest = hashlib.sha256()
    downloaded = 0
    started = time.monotonic()
    try:
        hostname = (urllib.parse.urlparse(url).hostname or "").lower()
        headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
        if hostname in ZIMMERMAN_HOSTS:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "application/zip,application/octet-stream,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://ericzimmerman.github.io/",
            }
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
            content_length = response.headers.get("Content-Length")
            total_bytes = int(content_length) if content_length else None
            if total_bytes and total_bytes > MAX_DOWNLOAD_BYTES:
                raise ToolDownloadError("la descarga supera el limite de 512 MB")

            if on_progress:
                on_progress(0, total_bytes)

            with open(temp_path, "wb") as output:
                while True:
                    if time.monotonic() - started > DOWNLOAD_MAX_SECONDS:
                        raise ToolDownloadError("la descarga excedio 10 minutos; vuelve a intentarlo")
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > MAX_DOWNLOAD_BYTES:
                        raise ToolDownloadError("la descarga supera el limite de 512 MB")
                    output.write(chunk)
                    digest.update(chunk)
                    if on_progress:
                        on_progress(downloaded, total_bytes)

        if downloaded == 0:
            raise ToolDownloadError("el servidor devolvio un archivo vacio")
        if total_bytes is not None and downloaded != total_bytes:
            raise ToolDownloadError("descarga incompleta; vuelve a pulsar el boton para reintentar")

        if on_progress:
            on_progress(downloaded, downloaded)

        actual_sha256 = digest.hexdigest()
        if expected_sha256 and not hmac.compare_digest(
            actual_sha256.lower(), expected_sha256.lower()
        ):
            raise ToolDownloadError(
                "la verificacion SHA-256 fallo; el archivo no se abrira por seguridad"
            )
        return temp_path
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def _read_small_page(url, agent=USER_AGENT):
    request = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
        raw_page = response.read(MAX_SOURCE_PAGE_BYTES + 1)
        if len(raw_page) > MAX_SOURCE_PAGE_BYTES:
            raise ToolDownloadError("la pagina de descarga supera el limite permitido")
        charset = response.headers.get_content_charset() or "utf-8"
    return raw_page.decode(charset, errors="replace")


def _resolve_mediafire_url(page_url):
    parser = _MediaFireDownloadParser()
    parser.feed(_read_small_page(page_url))
    if not parser.download_url:
        raise ToolDownloadError("MediaFire no devolvio un enlace de descarga valido")

    resolved_url = urllib.parse.urljoin(page_url, parser.download_url)
    parsed_url = urllib.parse.urlparse(resolved_url)
    hostname = (parsed_url.hostname or "").lower()
    if parsed_url.scheme != "https" or not (
        hostname == "mediafire.com" or hostname.endswith(".mediafire.com")
    ):
        raise ToolDownloadError("MediaFire devolvio un dominio de descarga inesperado")
    return resolved_url


def _resolve_download_url(tool):
    page_url = tool.get("mediafire_page")
    fallback_url = tool.get("url")
    if page_url:
        try:
            return _resolve_mediafire_url(page_url)
        except (OSError, ToolDownloadError, urllib.error.URLError):
            if fallback_url:
                return fallback_url
            raise
    return fallback_url


def _safe_extract_archive(archive_path, target_dir):
    target_root = os.path.realpath(target_dir)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                member_path = os.path.realpath(os.path.join(target_root, member.filename))
                try:
                    common_root = os.path.commonpath([target_root, member_path])
                except ValueError as exc:
                    raise ToolDownloadError("el ZIP contiene una ruta insegura") from exc
                if common_root != target_root:
                    raise ToolDownloadError("el ZIP contiene una ruta insegura")

                file_type = (member.external_attr >> 16) & 0o170000
                if file_type == stat.S_IFLNK:
                    raise ToolDownloadError("el ZIP contiene un enlace simbolico inseguro")

            archive.extractall(target_root)
    except zipfile.BadZipFile as exc:
        raise ToolDownloadError("el archivo descargado no es un ZIP valido") from exc


def _is_zimmerman(tool):
    """True para paquetes descargados del sitio oficial de Eric Zimmerman."""
    host = (urllib.parse.urlparse(tool.get("url") or "").hostname or "").lower()
    return host == "download.ericzimmermanstools.com"


def _package_root(full_path, tool):
    """Carpeta raiz del paquete (primer componente de tool['path'])."""
    parts = [p for p in tool.get("path", "").replace("\\", "/").split("/") if p]
    root = full_path
    for _ in range(max(len(parts) - 1, 0)):
        root = os.path.dirname(root)
    return root


def _normalized_name(text):
    return "".join(ch for ch in text.lower() if ch.isalnum())


def _find_executable(search_root, file_name, tool_name=""):
    """Busca el .exe por su nombre dentro de lo extraido, sin importar la estructura del ZIP."""
    if not os.path.isdir(search_root):
        return None
    wanted = file_name.lower()
    wanted_stem = _normalized_name(os.path.splitext(file_name)[0])
    tool_stem = _normalized_name(tool_name)
    exact, loose = [], []
    for current, directories, files in os.walk(search_root):
        directories.sort()
        depth = os.path.relpath(current, search_root).count(os.sep)
        for name in sorted(files):
            if not name.lower().endswith(".exe"):
                continue
            candidate = os.path.join(current, name)
            if name.lower() == wanted:
                exact.append((depth, candidate))
            elif _normalized_name(os.path.splitext(name)[0]) in (wanted_stem, tool_stem):
                loose.append((depth, candidate))
    for group in (exact, loose):
        if group:
            return min(group)[1]
    return None


def _unblock_tree(root):
    """Quita Mark of the Web de EXE/DLL para que Windows no bloquee el lanzamiento."""
    if not sys.platform.startswith("win"):
        return
    for current, _directories, files in os.walk(root):
        for name in files:
            if name.lower().endswith((".exe", ".dll")):
                try:
                    os.remove(os.path.join(current, name) + ":Zone.Identifier")
                except OSError:
                    pass


def _zimmerman_urls(tool):
    url = tool["url"]
    urls = [url]
    if url.startswith(ZIMMERMAN_PRIMARY):
        urls.append(ZIMMERMAN_MIRROR + url[len(ZIMMERMAN_PRIMARY):])
    return urls


def _discover_zimmerman_urls(tool):
    """Lee las paginas oficiales y devuelve los enlaces vigentes del mismo ZIP."""
    url = tool["url"]
    wanted = url.rsplit("/", 1)[1].lower()
    want_net9 = "/net9/" in url
    found = []
    for page in ZIMMERMAN_INDEX_PAGES:
        try:
            text = _read_small_page(page, "Mozilla/5.0")
        except (OSError, ToolDownloadError, urllib.error.URLError, ValueError):
            continue
        for match in re.finditer(r"https://[^\s\"'<>()\[\]|]+?\.zip", text, re.I):
            link = match.group(0)
            if link.startswith(ZIMMERMAN_MIRROR):
                link = ZIMMERMAN_PRIMARY + link[len(ZIMMERMAN_MIRROR):]
            if link.rsplit("/", 1)[-1].lower() != wanted:
                continue
            if ("/net9/" in link) != want_net9 or link in found:
                continue
            found.append(link)
    return found


def _download_zimmerman_zip(tool, target_dir, on_progress=None):
    from core import zimmerman_fetch

    zip_name = tool["url"].rsplit("/", 1)[1]
    category_dir = os.path.dirname(target_dir)
    try:
        return zimmerman_fetch.fetch_zip(
            _zimmerman_urls(tool),
            zip_name,
            target_dir,
            python_download=lambda url: _download_to_temp(
                url, target_dir, tool.get("sha256"), on_progress=on_progress
            ),
            discover=lambda: _discover_zimmerman_urls(tool),
            manual_dir=os.path.join(category_dir, "_manual_zips"),
            log_path=os.path.join(category_dir, "ultimo_error_descarga.log"),
        )
    except zimmerman_fetch.FetchError as exc:
        raise ToolDownloadError(str(exc)) from exc


def _download_tool(category_id, tool, full_path, on_progress=None):
    if not full_path:
        raise ToolDownloadError("esta herramienta no tiene una ruta de instalacion configurada")

    target_dir = os.path.dirname(full_path)
    if tool.get("archive_entry"):
        # ZIPs may contain an application subfolder. Extract at the package root,
        # not beside the nested EXE, and keep each tool's DLLs isolated.
        target_dir = full_path
        for _ in tool["archive_entry"].replace("\\", "/").split("/"):
            target_dir = os.path.dirname(target_dir)
    zimmerman = _is_zimmerman(tool)
    if zimmerman:
        target_dir = _package_root(full_path, tool)
    embedded_script = tool.get("embedded_script")
    if embedded_script is not None:
        os.makedirs(target_dir, exist_ok=True)
        file_descriptor, temp_path = tempfile.mkstemp(prefix=".sstool-script-", dir=target_dir)
        try:
            with os.fdopen(file_descriptor, "wb") as script_file:
                script_file.write(embedded_script.encode("utf-8"))
            _validate_payload(temp_path, tool)
            os.replace(temp_path, full_path)
            temp_path = None
            _write_install_marker(full_path, tool)
            return full_path
        finally:
            if temp_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    url = _resolve_download_url(tool)
    if not url:
        raise ToolDownloadError("esta herramienta todavia no tiene enlace de descarga")
    if zimmerman:
        temp_path = _download_zimmerman_zip(tool, target_dir, on_progress)
    else:
        temp_path = _download_to_temp(
            url, target_dir, tool.get("sha256"), on_progress=on_progress
        )
    try:
        if tool.get("archive"):
            if zimmerman:
                # Los paquetes se reinstalan limpios: nada de DLL viejas mezcladas.
                try:
                    os.remove(full_path)
                except OSError:
                    pass
            else:
                try:
                    os.remove(full_path)
                except FileNotFoundError:
                    pass
            _safe_extract_archive(temp_path, target_dir)
            if zimmerman and not os.path.isfile(full_path):
                found = _find_executable(
                    target_dir, os.path.basename(full_path), tool.get("name", "")
                )
                if not found:
                    raise ToolDownloadError(
                        f"{os.path.basename(full_path)} no esta dentro del ZIP oficial descargado"
                    )
                full_path = found
        else:
            os.replace(temp_path, full_path)
            temp_path = None

        try:
            _validate_payload(full_path, tool)
            expected_installed = _installed_sha256(tool)
            if expected_installed and not hmac.compare_digest(
                _sha256(full_path).lower(), expected_installed.lower()
            ):
                raise ToolDownloadError(
                    "el ejecutable instalado no coincide con el hash esperado"
                )
        except (OSError, ToolDownloadError):
            try:
                os.remove(full_path)
            except OSError:
                pass
            raise
        if zimmerman:
            _unblock_tree(target_dir)
        else:
            _mark_as_downloaded(full_path)
        _write_install_marker(full_path, tool)
        return full_path
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _previous_install(full_path, tool):
    """Copia ya instalada y verificada por este launcher (solo paquetes Zimmerman)."""
    if not _is_zimmerman(tool) or not full_path:
        return None
    candidate = full_path
    if not os.path.isfile(candidate):
        candidate = _find_executable(
            _package_root(full_path, tool), os.path.basename(full_path), tool.get("name", "")
        )
    if candidate and _is_valid_install(candidate, dict(tool, always_download=False)):
        return candidate
    return None


def _powershell_executable():
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidate = os.path.join(
        system_root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe"
    )
    return candidate if os.path.isfile(candidate) else "powershell.exe"


def _cmd_executable():
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidate = os.path.join(system_root, "System32", "cmd.exe")
    return candidate if os.path.isfile(candidate) else "cmd.exe"


def _tool_command(full_path, tool):
    if tool and tool.get("runner") == "zimmerman_cli":
        from core.zimmerman_runner import console_arguments
        return [_powershell_executable()] + console_arguments(full_path, tool)
    if tool and tool.get("native_command"):
        return [tool["native_command"]]
    if tool and tool.get("cmd_command"):
        # Mantiene literalmente las comillas del comando solicitado. Pasarlo
        # como lista haria que subprocess volviera a escapar el -Command de
        # PowerShell antes de entregarlo a cmd.exe.
        return (
            f"{subprocess.list2cmdline([_cmd_executable()])} "
            f"/d /k {tool['cmd_command']}"
        )
    if tool and tool.get("runner") == "powershell":
        powershell_command = [
            _powershell_executable(),
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            full_path,
        ]
        return [
            _cmd_executable(),
            "/d",
            "/k",
            subprocess.list2cmdline(powershell_command),
        ]
    return [full_path]


def _run_tool(full_path, tool=None):
    command = _tool_command(full_path, tool)
    working_directory = os.path.dirname(full_path) if full_path else _base_dir()
    if tool and tool.get("run_as_admin") and sys.platform.startswith("win"):
        if isinstance(command, str) and tool.get("cmd_command"):
            _run_command_elevated(
                _cmd_executable(),
                [],
                working_directory,
                raw_arguments=f"/d /k {tool['cmd_command']}",
            )
        else:
            _run_command_elevated(command[0], command[1:], working_directory)
        return True
    popen_kwargs = {"cwd": working_directory}
    needs_console = tool and (
        tool.get("runner") == "powershell" or tool.get("cmd_command")
    )
    if needs_console and sys.platform.startswith("win"):
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    try:
        subprocess.Popen(command, **popen_kwargs)
        return False
    except OSError as exc:
        if not sys.platform.startswith("win") or getattr(exc, "winerror", None) != 740:
            raise
        if isinstance(command, str) and tool and tool.get("cmd_command"):
            _run_command_elevated(
                _cmd_executable(),
                [],
                working_directory,
                raw_arguments=f"/d /k {tool['cmd_command']}",
            )
        else:
            _run_command_elevated(command[0], command[1:], working_directory)
        return True


def _run_tool_elevated(full_path):
    """Solicita elevacion mediante el UAC oficial de Windows."""
    _run_command_elevated(full_path, [], os.path.dirname(full_path))


def _run_command_elevated(
    executable, arguments, working_directory, raw_arguments=None
):
    """Ejecuta un comando mediante el verbo oficial runas de Windows."""
    import ctypes

    shell_execute = ctypes.windll.shell32.ShellExecuteW
    shell_execute.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_int,
    ]
    shell_execute.restype = ctypes.c_void_p
    result = shell_execute(
        None,
        "runas",
        executable,
        raw_arguments
        if raw_arguments is not None
        else (subprocess.list2cmdline(arguments) if arguments else None),
        working_directory,
        1,
    )
    result_code = int(result or 0)
    if result_code <= 32:
        raise ToolDownloadError(
            f"Windows no pudo iniciar el archivo (ShellExecute: {result_code}). "
            "Comprueba el aviso UAC, las dependencias y el historial de proteccion de Windows."
        )


def launch_tool(
    category_id,
    tool,
    on_missing=None,
    on_error=None,
    on_status=None,
    on_progress=None,
):
    """Descarga la herramienta si hace falta y despues la abre automaticamente."""
    name = tool.get("name", "Herramienta")
    full_path = resolve_tool_path(category_id, tool)
    direct_command = tool.get("cmd_command")
    native_command = tool.get("native_command")
    browser_url = tool.get("browser_url")
    configured = bool(
        direct_command
        or native_command
        or browser_url
        or (full_path and (tool.get("url") or tool.get("embedded_script") is not None))
    )

    try:
        if browser_url:
            opened = webbrowser.open_new_tab(browser_url)
            if not opened:
                raise ToolDownloadError("Windows no pudo abrir el navegador predeterminado")
            if on_status:
                on_status(f"{name} se abrio en el navegador.")
            return True

        if direct_command or native_command:
            elevated = _run_tool(None, tool)
            if on_status:
                if elevated:
                    on_status(f"{name} solicito permisos de administrador mediante UAC.")
                else:
                    on_status(f"{name} se abrio en CMD como administrador.")
            return True

        if _is_valid_install(full_path, tool):
            elevated = _run_tool(full_path, tool)
            if on_status:
                if elevated:
                    on_status(f"{name} solicito permisos de administrador mediante UAC.")
                else:
                    on_status(f"{name} se abrio correctamente.")
            return True

        if configured:
            if on_status:
                on_status(f"Descargando y verificando {name}...")
            try:
                full_path = _download_tool(
                    category_id, tool, full_path, on_progress=on_progress
                )
            except (OSError, ToolDownloadError, urllib.error.URLError):
                previous = _previous_install(full_path, tool)
                if not previous:
                    raise
                full_path = previous
                if on_status:
                    on_status(f"No se pudo actualizar {name}; se abre la copia ya descargada.")
            elevated = _run_tool(full_path, tool)
            if on_status:
                if elevated:
                    on_status(
                        f"{name} se descargo y solicito permisos de administrador mediante UAC."
                    )
                else:
                    on_status(f"{name} se descargo y se abrio correctamente.")
            return True

        if tool.get("url"):
            webbrowser.open(tool["url"])
            return True

        if on_missing:
            expected = full_path or "(sin path configurado)"
            on_missing(
                f"'{name}' todavia no tiene funcion configurada.\n"
                f"Ruta esperada:\n{expected}"
            )
        return False
    except (OSError, ToolDownloadError, urllib.error.URLError) as exc:
        if on_error:
            on_error(f"No se pudo descargar o iniciar {name}:\n{exc}")
        return False


def open_tools_folder(category_id=None):
    base = ensure_tools_root()
    target = os.path.join(base, category_id) if category_id else base
    os.makedirs(target, exist_ok=True)

    if sys.platform.startswith("win"):
        os.startfile(target)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])
