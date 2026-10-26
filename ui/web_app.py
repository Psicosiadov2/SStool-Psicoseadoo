"""Local HTML frontend; the browser can dispatch only catalogued tools."""
import json
import base64
import html
import re
import threading
import time
import webbrowser
from pathlib import Path

from core.data import CATEGORIES
from core.i18n import category_label, tool_description
from core.launcher import launch_tool
from core.windows_shell import asset_path


def catalogue():
    return [dict(id=c['id'], labels={l: category_label(c, l) for l in ('en', 'es')},
                 tools=[dict(id=t.get("id", f"{c['id']}:{i}"), name=t['name'],
                             descriptions={l: tool_description(t, l) for l in ('en', 'es')})
                        for i, t in enumerate(c['tools'])]) for c in CATEGORIES]


def document():
    page = Path(asset_path('interface-template.html')).read_text(encoding='utf-8')
    data = json.dumps(catalogue(), ensure_ascii=True).replace('<', '\\u003c')
    page = re.sub(r"const catalogue=.*?(?=const categoryImages)", lambda _: 'const catalogue=' + data + ';\n', page, count=1, flags=re.S)
    page = page.replace('PsicoseadoSSTool', 'SSTool+')
    motion = Path(asset_path('motion.js')).read_text(encoding='utf-8')
    style = '<style>.mouse-trail{position:fixed;left:0;top:0;width:90px;height:20px;border-radius:50%;pointer-events:none;z-index:65;background:radial-gradient(ellipse,#ffffff40,transparent 70%);filter:blur(6px);opacity:0;transform-origin:center}.tab,.card,.controls button,.search-link{transition:background-color .18s,border-color .18s,color .18s}.titlebar{cursor:grab}.titlebar button{cursor:pointer}.title-brand{flex:1;height:100%;display:flex;flex-direction:column;justify-content:center}.title-brand span{pointer-events:none}</style>'
    return page.replace('</head>', style + '</head>').replace('</body>', '<script>' + motion + '</script></body>')


class Bridge:
    def __init__(self):
        self._window = None
        self._lock = threading.Lock()
        self._busy = set()
        self._until = {}
        self._slots = threading.Semaphore(2)
        self._events = {}
        self._event_lock = threading.Lock()
        self._tools = {t.get("id", f"{c['id']}:{i}"): (t.get("storage_category", c['id']), t) for c in CATEGORIES for i, t in enumerate(c['tools'])}
        self._maximized = False
        self._fullscreen = False

    def _emit(self, payload):
        # Workers must never wait for the renderer (especially while minimized).
        # Coalesce progress: memory stays bounded even if the UI stops polling.
        with self._event_lock:
            key = (payload['id'], payload['kind'])
            self._events.pop(key, None)
            self._events[key] = payload

    def poll_events(self):
        with self._event_lock:
            events = list(self._events.values())
            self._events.clear()
        return events

    def launch(self, tool_id):
        if not isinstance(tool_id, str) or tool_id not in self._tools:
            return {'accepted': False, 'error': 'Unknown tool'}
        with self._lock:
            if len(self._busy) >= 2:
                return {'accepted': False, 'error': 'Two tools are already opening. Please wait.'}
            if tool_id in self._busy or time.monotonic() < self._until.get(tool_id, 0):
                return {'accepted': False, 'error': 'Please wait'}
            self._busy.add(tool_id)
            self._until[tool_id] = time.monotonic() + 5
        try:
            threading.Thread(target=self._run, args=(tool_id,), daemon=True).start()
        except Exception:
            with self._lock:
                self._busy.discard(tool_id)
                self._until.pop(tool_id, None)
            return {'accepted': False, 'error': 'Unable to start the tool. Please retry.'}
        return {'accepted': True}

    def _run(self, tool_id):
        cid, tool = self._tools[tool_id]
        last = [0.0]
        ok = False
        def status(message):
            self._emit(dict(kind='status', id=tool_id, message=str(message)))
        def progress(done, total):
            now = time.monotonic()
            if now - last[0] < .08 and done != total:
                return
            last[0] = now
            self._emit(dict(kind='progress', id=tool_id, name=tool['name'],
                            downloaded_bytes=done, total_bytes=total,
                            percent=min(100, done * 100 / total) if total else None))
        try:
            with self._slots:
                ok = launch_tool(cid, tool, on_missing=status, on_error=status,
                                 on_status=status, on_progress=progress)
        except Exception as exc:
            status(str(exc))
            ok = False
        finally:
            with self._lock:
                self._busy.discard(tool_id)
            self._emit(dict(kind='done', id=tool_id, ok=ok))

    def window_control(self, action):
        if action == 'minimize':
            self._window.minimize()
        elif action == 'maximize':
            if self._fullscreen:
                self._window.toggle_fullscreen()
                self._fullscreen = False
                return True
            if self._maximized:
                self._window.restore()
            else:
                self._window.maximize()
            self._maximized = not self._maximized
        elif action == 'fullscreen':
            self._window.toggle_fullscreen()
            self._fullscreen = not self._fullscreen
        elif action == 'exit-fullscreen':
            if self._fullscreen:
                self._window.toggle_fullscreen()
                self._fullscreen = False
        elif action == 'close':
            self._window.destroy()
        else:
            return False
        return True

    def open_link(self, target):
        urls = {'github': 'https://github.com/Psicosiadov2/', 'discord': 'https://discord.gg/bhD5sheFf4'}
        if target not in urls:
            return False
        return webbrowser.open_new_tab(urls[target])


def run():
    import os
    import webview
    # WebView2 must use a writable profile, never the onefile extraction folder.
    profile = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'PsicoseadoSSTool' / 'WebView2'
    profile.mkdir(parents=True, exist_ok=True)
    # NavigateToString has a size limit; embedded artwork makes this page large.
    page = profile.parent / 'interface.html'
    page.write_text(document(), encoding='utf-8')
    bridge = Bridge()
    bridge._fullscreen = False
    webview.settings['DRAG_REGION_SELECTOR'] = '.pywebview-drag-region'
    webview.settings['DRAG_REGION_DIRECT_TARGET_ONLY'] = True
    bridge._window = webview.create_window(
        'SSTool+', url=page.as_uri(), js_api=bridge,
        width=1180, height=820, min_size=(760, 540), frameless=True,
        easy_drag=False, resizable=True, fullscreen=False, background_color='#080808')
    def remove_native_frame():
        import sys
        if sys.platform != 'win32':
            return
        native = bridge._window.native
        # Fullscreen/restore can reset WinForms' border; reapply on transitions.
        from System import Action
        from System.Windows.Forms import FormBorderStyle
        borderless = getattr(FormBorderStyle, 'None')
        def enforce(*_):
            if native.FormBorderStyle != borderless:
                native.FormBorderStyle = borderless
        def install():
            # Sin icono personalizado en la ventana/ejecutable (solicitado).
            enforce()
            native.StyleChanged += enforce
            native.SizeChanged += enforce
        native.Invoke(Action(install))
    bridge._window.events.shown += remove_native_frame
    webview.start(gui='edgechromium', debug=False, storage_path=str(profile))
