param(
    [Parameter(Mandatory=$true)][switch]$NativeSlotAllocated,
    [Parameter(Mandatory=$true)][string]$View,
    [Parameter(Mandatory=$true)][string]$RuntimeRepo,
    [Parameter(Mandatory=$true)][string]$Dependencies,
    [Parameter(Mandatory=$true)][string]$Dosbox,
    [Parameter(Mandatory=$true)][string]$WindowsTemplate,
    [Parameter(Mandatory=$true)][string]$Output,
    [string]$ReuseNative,
    [string]$Python = 'python.exe',
    [ValidateRange(30,600)][int]$Seconds = 600,
    [string]$LockPath = 'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock'
)
$ErrorActionPreference='Stop'
if (!$NativeSlotAllocated) { throw 'Native allocation required.' }
$lease=$null
$child=$null
$started=$null
try {
    $lease=[IO.File]::Open($LockPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    $lease.Lock(0,1)
    $env:DISPLAY3_LEASE_HELD='1'
    $nativeArgs=@('-B',(Join-Path $PSScriptRoot 'NATIVE.PY'),'--view',$View,'--runtime-repo',$RuntimeRepo,'--deps',$Dependencies,
            '--dosbox',$Dosbox,'--windows-template',$WindowsTemplate,'--out',$Output)
    if ($ReuseNative) { $nativeArgs += @('--reuse-native',$ReuseNative) }
    $quoted=($nativeArgs | ForEach-Object { '"'+$_+'"' }) -join ' '
    $log=$Output+'.worker.log'
    $err=$Output+'.worker.err'
    $child=Start-Process -FilePath $Python -ArgumentList $quoted -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $log -RedirectStandardError $err
    $started=$child.StartTime
    Write-Output ('LEASE ACQUIRED; OWNED PID '+$child.Id+'; '+$Seconds+' seconds')
    if (!$child.WaitForExit($Seconds*1000)) { throw 'Owned qualification exceeded allocated deadline.' }
    $child.Refresh()
    if ($child.ExitCode -ne 0) { throw ('Qualification failed; exit '+$child.ExitCode+'; see '+$err) }
    Write-Output ('PASS '+(Join-Path $Output 'NATIVE.JSN'))
} finally {
    if ($child) {
        $child.Refresh()
        if (!$child.HasExited) {
            $current=Get-Process -Id $child.Id -ErrorAction SilentlyContinue
            if ($current -and $current.StartTime -eq $started) {
                & taskkill.exe /PID $child.Id /T /F | Out-Null
                $child.WaitForExit(5000) | Out-Null
            }
        }
        $child.Dispose()
    }
    Remove-Item Env:\DISPLAY3_LEASE_HELD -ErrorAction SilentlyContinue
    if ($lease) {
        try { $lease.Unlock(0,1) } finally { $lease.Dispose() }
        Write-Output 'LEASE RELEASED'
    }
}
