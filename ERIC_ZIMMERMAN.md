# Eric Zimmerman in SSTool+

The category includes all 26 programs listed under **Forensic tools** on the official site, checked on 2026-10-14:
https://ericzimmerman.github.io/

GUI: EZViewer, Hasher, JumpList Explorer, MFTExplorer, Registry Explorer,
SDB Explorer, ShellBags Explorer, Timeline Explorer.

CLI: AmcacheParser, AppCompatCacheParser, bstrings, EvtxECmd, JLECmd, LECmd,
MFTECmd, PECmd, RBCmd, RecentFileCacheParser, RECmd, RLA, SBECmd, SQLECmd,
SrumECmd, SumECmd, VSCMount, WxTCmd.

All programs launch with Windows administrator approval (UAC).

Executable lookup: each ZIP is extracted completely into its own folder and the
executable is then located **by its file name** (case-insensitive, shallowest match),
so it works whatever internal folder layout the official ZIP has. If
download.ericzimmermanstools.com fails, the same file is requested from Eric's
official storage bucket (f001.backblazeb2.com/file/EricZimmermanTools). If an update
cannot be downloaded but a verified copy exists, that copy is launched instead.
Files are extracted by SSTool+ (no Mark of the Web on EXE/DLL), as the official site
recommends not extracting with Windows Explorer. Each package is downloaded
from the official current ZIP URL when clicked, extracted into its own folder, and
keeps its DLLs, maps and auxiliary files. The ZIPs are not bundled in SSTool+.

Most use .NET 9; install the .NET 9 Desktop Runtime from Dependencies if required.
Hasher is the author's available .NET 4 build and requires .NET Framework 4.7.2 or newer.

GUI tools open directly. CLI tools open an elevated PowerShell console, show the
downloaded tool's current --help, then ask for arguments. Quote evidence/output paths
containing spaces. The entered text is parsed as Windows arguments, never evaluated
as a shell script. The console stays open to show results and errors.

SrumECmd has a guided workflow: choose SRUDB.dat, optionally choose the SOFTWARE
registry hive, and select a CSV output folder. It passes -f, --csv, and optional -r.
Use collected evidence copies if a running Windows database is locked. The tool's
output goes into a timestamped subfolder of the chosen destination.

Other CLI tools need case-specific parameters from their displayed help: select the
appropriate input file/directory, output format/directory, maps, filters or mounting
options. There is no single command that correctly handles every evidence set.

The catalog excludes the official site's separate **Other tools** section (such as
KAPE, TimeApp, iisGeoLocate and XWFIM). Native execution still needs Windows testing.

## Download methods (in order)
For every ZIP: Python (browser headers) -> curl.exe -> PowerShell Invoke-WebRequest -> BITS,
tried against the official host, the official storage bucket, the live link read from the
official pages, and finally the Chocolatey package that embeds the same official ZIP.
If everything fails, a ZIP placed in `tools/ericzimmerman/_manual_zips/` is used and every
attempt is written to `tools/ericzimmerman/ultimo_error_descarga.log`.
