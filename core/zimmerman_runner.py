"""Keep forensic CLI tools in an elevated console with explicit input arguments."""
import base64
from pathlib import Path


SCRIPT = r'''
$ErrorActionPreference = 'Stop'
$tool = __EXE__
Set-Location -LiteralPath (Split-Path -Parent $tool)
try {
    Write-Host ('SSTool+ - ' + [IO.Path]::GetFileName($tool)) -ForegroundColor Cyan
    & $tool --help
    if (__SRUM__) {
        Add-Type -AssemblyName System.Windows.Forms
        $pick = New-Object System.Windows.Forms.OpenFileDialog
        $pick.Title = 'Select SRUDB.dat (a collected copy if the live database is locked)'
        $pick.Filter = 'SRUM database|SRUDB.dat|All files|*.*'
        if ($pick.ShowDialog() -ne 'OK') { return }
        $source = $pick.FileName
        $pick.Title = 'Optional SOFTWARE registry hive - Cancel to skip'
        $pick.Filter = 'All files|*.*'
        $registry = $null
        if ($pick.ShowDialog() -eq 'OK') { $registry = $pick.FileName }
        $pick.Dispose()
        $out = New-Object System.Windows.Forms.FolderBrowserDialog
        $out.Description = 'Select a folder for SRUM CSV results'
        if ($out.ShowDialog() -ne 'OK') { return }
        $destination = Join-Path $out.SelectedPath ('SrumECmd-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
        $out.Dispose()
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        $toolArgs = @('-f', $source, '--csv', $destination)
        if ($registry) { $toolArgs += @('-r', $registry) }
        Write-Host ('Output: ' + $destination) -ForegroundColor Cyan
    } else {
        Write-Host 'Use the options shown above to select evidence files, folders and output.' -ForegroundColor Cyan
        Write-Host 'Quote paths containing spaces. Enter submits options; blank cancels.'
        $line = Read-Host 'Tool arguments'
        if ([string]::IsNullOrWhiteSpace($line)) { return }
        # Windows argument parsing preserves quoted paths; no shell evaluation.
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class SSToolArgv {
 [DllImport("shell32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
 static extern IntPtr CommandLineToArgvW(string text, out int count);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr ptr);
 public static string[] Parse(string text) {
  int count; IntPtr p = CommandLineToArgvW("tool " + text, out count);
  if (p == IntPtr.Zero) throw new ArgumentException("Invalid arguments");
  try { var a = new string[count-1]; for(int i=1;i<count;i++)
    a[i-1] = Marshal.PtrToStringUni(Marshal.ReadIntPtr(p, i*IntPtr.Size)); return a;
  } finally { LocalFree(p); }
 }
}
'@
        $toolArgs = [SSToolArgv]::Parse($line)
    }
    & $tool @toolArgs
    Write-Host ('Tool exit code: ' + $LASTEXITCODE) -ForegroundColor Cyan
} catch { Write-Host $_.Exception.Message -ForegroundColor Red }
'''


def console_arguments(full_path, tool):
    exe = "'" + str(Path(full_path)).replace("'", "''") + "'"
    script = SCRIPT.replace('__EXE__', exe).replace('__SRUM__', '$true' if tool['name'] == 'SrumECmd' else '$false')
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    return ['-NoLogo', '-NoProfile', '-NoExit', '-STA', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encoded]
