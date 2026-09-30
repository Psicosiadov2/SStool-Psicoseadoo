"""Descarga, verifica y ejecuta las herramientas conectadas a cada tarjeta."""

import hashlib
import hmac
import json
import os
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from html.parser import HTMLParser

from core.config import TOOLS_ROOT


DOWNLOAD_TIMEOUT = 120
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
USER_AGENT = "PsicoseadoSSTool/1.0 (Windows tool launcher)"
MAX_SCRIPT_BYTES = 8 * 1024 * 1024
MAX_SOURCE_PAGE_BYTES = 2 * 1024 * 1024
INSTALL_MARKER_SUFFIX = ".psicoseado-sstool.json"
INSTALL_MARKER_SCHEMA = 1


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


def resolve_tool_path(category_id, tool):
    """Ruta absoluta esperada del ejecutable de una herramienta."""
    path = tool.get("path")
    if not path:
        return None
    return os.path.join(_base_dir(), TOOLS_ROOT, category_id, path)


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
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
            content_length = response.headers.get("Content-Length")
            total_bytes = int(content_length) if content_length else None
            if total_bytes and total_bytes > MAX_DOWNLOAD_BYTES:
                raise ToolDownloadError("la descarga supera el limite de 512 MB")

            if on_progress:
                on_progress(0, total_bytes)

            with open(temp_path, "wb") as output:
                while True:
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


def _read_small_page(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
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


def _download_tool(category_id, tool, full_path, on_progress=None):
    if not full_path:
        raise ToolDownloadError("esta herramienta no tiene una ruta de instalacion configurada")

    target_dir = os.path.dirname(full_path)
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
    temp_path = _download_to_temp(
        url, target_dir, tool.get("sha256"), on_progress=on_progress
    )
    try:
        if tool.get("archive"):
            try:
                os.remove(full_path)
            except FileNotFoundError:
                pass
            _safe_extract_archive(temp_path, target_dir)
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
        _mark_as_downloaded(full_path)
        _write_install_marker(full_path, tool)
        return full_path
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


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
            "Windows no concedio permisos de administrador o se cancelo el aviso UAC"
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
    configured = bool(
        direct_command
        or native_command
        or (full_path and (tool.get("url") or tool.get("embedded_script") is not None))
    )

    try:
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
            _download_tool(category_id, tool, full_path, on_progress=on_progress)
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
    base = os.path.join(_base_dir(), TOOLS_ROOT)
    target = os.path.join(base, category_id) if category_id else base
    os.makedirs(target, exist_ok=True)

    if sys.platform.startswith("win"):
        os.startfile(target)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])
