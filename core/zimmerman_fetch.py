"""Metodos alternativos para obtener los ZIP oficiales de Eric Zimmerman.

Orden de intentos para cada ZIP:
  1. Python (urllib) con cabeceras de navegador.
  2. curl.exe de Windows.
  3. PowerShell Invoke-WebRequest.
  4. BITS (Start-BitsTransfer).
Se prueba con el sitio oficial, el almacen oficial (Backblaze), el enlace vigente
leido de las paginas oficiales y, por ultimo, el paquete de Chocolatey (que incluye
el mismo ZIP oficial). Si todo falla se usa un ZIP puesto manualmente en
``_manual_zips`` y se guarda un log con cada intento.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REFERER = "https://ericzimmerman.github.io/"
CHOCOLATEY_API = "https://community.chocolatey.org/api/v2/package/"
MAX_BYTES = 512 * 1024 * 1024
EXTERNAL_TIMEOUT = 600
CREATE_NO_WINDOW = 0x08000000


class FetchError(RuntimeError):
    pass


def _flags():
    return CREATE_NO_WINDOW if sys.platform.startswith("win") else 0


def _system32(*parts):
    return os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", *parts)


def _run(command, env=None):
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=EXTERNAL_TIMEOUT,
            env=env, creationflags=_flags(), shell=False,
        )
    except subprocess.TimeoutExpired:
        raise FetchError("tiempo de espera agotado")
    except OSError as exc:
        raise FetchError(str(exc))
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().replace("\n", " ")
        raise FetchError(detail[:200] or f"codigo de salida {result.returncode}")


def _curl(url, dest):
    exe = _system32("curl.exe")
    if not os.path.isfile(exe):
        exe = shutil.which("curl.exe") or shutil.which("curl")
    if not exe:
        raise FetchError("curl.exe no disponible")
    _run([
        exe, "-L", "--fail", "--silent", "--show-error", "--retry", "2",
        "--max-time", str(EXTERNAL_TIMEOUT), "--max-filesize", str(MAX_BYTES),
        "-A", BROWSER_UA, "-e", REFERER, "-o", dest, url,
    ])


def _powershell(script, url, dest):
    exe = _system32("WindowsPowerShell", "v1.0", "powershell.exe")
    if not os.path.isfile(exe):
        exe = shutil.which("powershell") or shutil.which("pwsh")
    if not exe:
        raise FetchError("PowerShell no disponible")
    env = dict(os.environ, SS_URL=url, SS_OUT=dest, SS_UA=BROWSER_UA, SS_REF=REFERER)
    _run([exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
          "-Command", script], env=env)


_TLS = "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;"


def _invoke_webrequest(url, dest):
    _powershell(
        "$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';" + _TLS +
        "Invoke-WebRequest -UseBasicParsing -Uri $env:SS_URL -OutFile $env:SS_OUT "
        "-UserAgent $env:SS_UA -Headers @{Referer=$env:SS_REF} -TimeoutSec 600",
        url, dest,
    )


def _bits(url, dest):
    _powershell(
        "$ErrorActionPreference='Stop';" + _TLS +
        "Start-BitsTransfer -Source $env:SS_URL -Destination $env:SS_OUT",
        url, dest,
    )


# Se puede reemplazar en los tests.
EXTERNAL_METHODS = (
    ("curl", _curl),
    ("powershell", _invoke_webrequest),
    ("bits", _bits),
)


def _valid_zip(path):
    try:
        size = os.path.getsize(path)
        return 0 < size <= MAX_BYTES and zipfile.is_zipfile(path)
    except OSError:
        return False


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _new_temp(target_dir):
    descriptor, path = tempfile.mkstemp(prefix=".sstool-download-", dir=target_dir)
    os.close(descriptor)
    return path


def _extract_inner_zip(package_path, zip_name, target_dir):
    """Los paquetes .nupkg de Chocolatey llevan dentro el ZIP oficial."""
    wanted = zip_name.lower()
    with zipfile.ZipFile(package_path) as package:
        for info in package.infolist():
            if os.path.basename(info.filename).lower() != wanted:
                continue
            if info.file_size <= 0 or info.file_size > MAX_BYTES:
                raise FetchError("el ZIP incluido en el paquete tiene un tamano no valido")
            inner = _new_temp(target_dir)
            try:
                with package.open(info) as source, open(inner, "wb") as output:
                    shutil.copyfileobj(source, output)
            except Exception:
                _remove(inner)
                raise
            if not _valid_zip(inner):
                _remove(inner)
                raise FetchError("el ZIP incluido en el paquete esta danado")
            return inner
    raise FetchError(f"el paquete no contiene {zip_name}")


def fetch_zip(urls, zip_name, target_dir, python_download, discover=None,
              manual_dir=None, log_path=None):
    """Devuelve la ruta temporal de un ZIP valido o lanza FetchError.

    python_download(url) -> ruta temporal (metodo 1, con progreso).
    discover() -> lista de URLs adicionales leidas de las paginas oficiales.
    """
    os.makedirs(target_dir, exist_ok=True)
    attempts = []
    tried = set()

    def host(url):
        return url.split("/")[2] if "//" in url else url

    def fetch_url(url, label):
        """Prueba todos los metodos con una URL. Devuelve ruta temporal o None."""
        methods = [("python", None)] + list(EXTERNAL_METHODS)
        for name, function in methods:
            path = None
            try:
                if function is None:
                    path = python_download(url)
                else:
                    path = _new_temp(target_dir)
                    _remove(path)  # BITS/curl crean el destino ellos mismos
                    function(url, path)
                if _valid_zip(path):
                    return path
                raise FetchError("la respuesta no es un ZIP valido")
            except Exception as exc:  # noqa: BLE001 - se registra y se prueba el siguiente
                attempts.append(f"{label} [{name}]: {exc}")
                if path:
                    _remove(path)
        return None

    def try_urls(url_list):
        for url in url_list:
            if url in tried:
                continue
            tried.add(url)
            path = fetch_url(url, host(url))
            if path:
                return path
        return None

    found = try_urls(urls)
    if not found and discover:
        try:
            extra = discover()
        except Exception as exc:  # noqa: BLE001
            attempts.append(f"paginas oficiales: {exc}")
            extra = []
        found = try_urls(extra)

    if not found:
        choco_url = CHOCOLATEY_API + os.path.splitext(zip_name)[0].lower()
        package = fetch_url(choco_url, "chocolatey")
        if package:
            try:
                found = _extract_inner_zip(package, zip_name, target_dir)
            except Exception as exc:  # noqa: BLE001
                attempts.append(f"chocolatey [paquete]: {exc}")
            finally:
                _remove(package)

    if not found and manual_dir:
        os.makedirs(manual_dir, exist_ok=True)
        for name in os.listdir(manual_dir):
            candidate = os.path.join(manual_dir, name)
            if name.lower() == zip_name.lower() and _valid_zip(candidate):
                copy = _new_temp(target_dir)
                shutil.copyfile(candidate, copy)
                attempts.append(f"usado ZIP manual: {candidate}")
                found = copy
                break

    if found:
        return found

    if log_path:
        try:
            with open(log_path, "w", encoding="utf-8") as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {zip_name}\n")
                log.write("\n".join(attempts) + "\n")
        except OSError:
            pass
    first = attempts[0] if attempts else "sin detalle"
    hint = f" Detalle en {log_path}." if log_path else ""
    manual = (
        f" Alternativa: descarga {zip_name} desde https://ericzimmerman.github.io "
        f"en tu navegador y copialo en {manual_dir}."
        if manual_dir else ""
    )
    raise FetchError(f"no se pudo obtener {zip_name} ({first}).{hint}{manual}")
