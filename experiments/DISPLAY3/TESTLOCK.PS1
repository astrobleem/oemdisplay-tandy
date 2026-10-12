# MIT, Copyright (c) 2026 Windows XT contributors.
# Synthetic host refusals only. Worker executable deliberately does not exist.
$ErrorActionPreference='Stop'
$wrapper=Join-Path $PSScriptRoot 'NATIVE.PS1'
$tokens=$null
$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($wrapper,[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count) { throw 'Wrapper parse failure.' }
$lockParameter=$ast.ParamBlock.Parameters | Where-Object { $_.Name.VariablePath.UserPath -eq 'LockPath' }
$metadata=(Get-Command $wrapper).Parameters['LockPath'].Attributes |
    Where-Object { $_ -is [Management.Automation.ParameterAttribute] }
if (!$lockParameter -or $lockParameter.DefaultValue -or !$metadata.Mandatory) {
    throw 'LockPath must be mandatory without a host-specific default.'
}
Write-Output 'PASS explicit mandatory lock path'
$tempBase=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$fixture=[IO.Path]::GetFullPath((Join-Path $tempBase ('display3-lock-'+[Guid]::NewGuid().ToString('N'))))
$handle=$null
try {
    [IO.Directory]::CreateDirectory($fixture) | Out-Null
    $output=Join-Path $fixture 'OUTPUT'
    $arguments=@{NativeSlotAllocated=$true; View=$fixture; RuntimeRepo=$fixture; Dependencies=$fixture;
        Dosbox=(Join-Path $fixture 'NOEMU.EXE'); WindowsTemplate=$fixture; Output=$output;
        Python=(Join-Path $fixture 'NOWORKER.EXE'); Seconds=30; LockPath=(Join-Path $fixture 'MISSING.LCK')}
    function Expect-Refusal([string]$name,[hashtable]$parameters,[bool]$allocationError=$false) {
        $caught=$null
        try { & $wrapper @parameters } catch { $caught=$_.Exception }
        if (!$caught) { throw ('Unexpected success: '+$name) }
        if ($allocationError) {
            if ($caught.Message -notmatch 'Native allocation required') { throw $caught }
        } else {
            while ($caught.InnerException) { $caught=$caught.InnerException }
            if ($caught -isnot [IO.IOException]) { throw $caught }
        }
        if ((Test-Path -LiteralPath $output) -or (Test-Path -LiteralPath ($output+'.worker.log')) -or
                (Test-Path -LiteralPath ($output+'.worker.err'))) { throw 'Worker path reached.' }
        Write-Output ('PASS '+$name+'; no worker/emulator launched')
    }
    Expect-Refusal 'missing explicit lock' $arguments
    $arguments.NativeSlotAllocated=$false
    Expect-Refusal 'missing allocation' $arguments $true
    $arguments.NativeSlotAllocated=$true
    $arguments.LockPath=Join-Path $fixture 'BUSY.LCK'
    $handle=[IO.File]::Open($arguments.LockPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    $handle.SetLength(1)
    Expect-Refusal 'busy explicit lock' $arguments
} finally {
    if ($handle) { $handle.Dispose() }
    $boundary=$tempBase.TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
    if (!$fixture.StartsWith($boundary,[StringComparison]::OrdinalIgnoreCase) -or
            [IO.Path]::GetFileName($fixture) -notmatch '^display3-lock-[0-9a-f]{32}$') {
        throw 'Refusing cleanup outside the owned synthetic fixture.'
    }
    if (Test-Path -LiteralPath $fixture) { Remove-Item -LiteralPath $fixture -Recurse -Force }
}
