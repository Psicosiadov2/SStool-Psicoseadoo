# SSTool+ performance update

- Reduced category transitions to one short opacity/transform animation. Removed duplicated grids and per-card animated blur.
- Cards no longer use backdrop blur. Low-effects mode activates for browsers reporting at most 4 logical CPU threads or 4 GB memory, or reduced-motion preference.
- Pointer effects batch updates once per rendered frame; expensive pointer effects are disabled in low-effects mode.
- Intro canvas uses a lower pixel density and fewer particles. A timer reveals the app independently of iframe loading, with a CSS fallback.
- At most two tools may open/download simultaneously. Additional clicks show a retry message instead of creating waiting threads.
- Download progress is coalesced in a bounded queue and polled by the UI. Download workers never wait for JavaScript execution.
- Downloads have a 30-second socket timeout and a 10-minute total deadline checked between reads. Incomplete downloads are removed.
- New magnifying-glass application icon.

## Platform scope

This package targets Windows 10/11 x64 with Microsoft Edge WebView2 Runtime. The catalog contains Windows executables and Windows-specific commands; this update does not make them executable on Linux, macOS, Android, or iOS. Individual third-party utilities may have additional requirements.

Build with BUILD_EXE.bat on Windows using Python 3.12 x64. Browser and automated tests do not replace testing the compiled executable on a low-resource Windows PC. Preview: open preview.html; tools launch only in the desktop app.
