<#
.SYNOPSIS
	sessionStart hook for the build-perf-cpp plugin: ensure a current vcperf.exe is available.

.DESCRIPTION
	Installs or updates the Microsoft.Cpp.vcperf NuGet package under
	%LOCALAPPDATA%\vcperf\build-perf-cpp. Each session contacts the public feed to pull the newest published version
	(NuGet skips the download if the same version is already installed).

	If the feed is unreachable, an already-installed version is used only when it
	meets the minimum version required for /jsonAnalysis support; otherwise an
	error is reported.
#>

$minVersion  = @(2, 9, 26072903)
$installDir  = Join-Path $env:LOCALAPPDATA 'vcperf\build-perf-cpp'
$nugetSource = 'https://pkgs.dev.azure.com/azure-public/VisualCpp/_packaging/cpp_PublicPackages/nuget/v3/index.json'

function Get-VcperfVersionParts ([string]$dirName) {
	# Extracts numeric version components from a package directory name.
	$ver = $dirName -replace '^Microsoft\.Cpp\.vcperf\.', ''
	$ver.Split('.') | ForEach-Object { [long]$_ }
}

function Compare-VersionParts ([long[]]$a, [long[]]$b) {
	$max = [Math]::Max($a.Count, $b.Count)
	for ($i = 0; $i -lt $max; $i++) {
		$av = if ($i -lt $a.Count) { $a[$i] } else { 0 }
		$bv = if ($i -lt $b.Count) { $b[$i] } else { 0 }
		if ($av -ne $bv) { return $av.CompareTo($bv) }
	}
	return 0
}

function Get-VcperfDir {
	# Returns the package directory with the highest version that contains vcperf.exe.
	Get-ChildItem -Path $installDir -Directory -Filter 'Microsoft.Cpp.vcperf.*' -ErrorAction SilentlyContinue |
		Where-Object { Get-ChildItem -Path $_.FullName -Recurse -Filter 'vcperf.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 } |
		Sort-Object { (Get-VcperfVersionParts $_.Name | ForEach-Object { $_.ToString().PadLeft(20, '0') }) -join '.' } -Descending |
		Select-Object -First 1
}

# Require the NuGet CLI on PATH. The feed-auth procedure
# (skills/build-performance-analysis/references/feed-auth.md) installs it with
# 'winget install Microsoft.NuGet', which links nuget.exe onto PATH for new sessions.
if (-not (Get-Command nuget -ErrorAction SilentlyContinue)) {
	Write-Error "The NuGet CLI ('nuget') was not found on PATH. Install it with 'winget install Microsoft.NuGet' or download https://aka.ms/nugetclidl and add it to PATH."
	exit 1
}

New-Item -Path $installDir -ItemType Directory -Force | Out-Null

# Contact the feed and pull the newest published version.
# NuGet skips the download if the same version directory already exists.
$feedReached = $false
$nugetOutput = ''
try {
	$raw = & nuget install Microsoft.Cpp.vcperf -Source $nugetSource -OutputDirectory $installDir -NonInteractive 2>&1
	$nugetOutput = ($raw | Out-String).Trim()
	$feedReached = ($LASTEXITCODE -eq 0)
}
catch {
	$nugetOutput = $_.Exception.Message
}

$latest = Get-VcperfDir

if ($feedReached) {
	if (-not $latest) {
		Write-Error "vcperf install succeeded but no vcperf.exe was found under $installDir."
		exit 1
	}
	Write-Host "vcperf ready ($($latest.Name))."
}
elseif ($latest -and (Compare-VersionParts (Get-VcperfVersionParts $latest.Name) $minVersion) -ge 0) {
	Write-Warning "Could not reach the vcperf feed. Using installed $($latest.Name)."
}
else {
	$min = $minVersion -join '.'
	$reason = if ($latest) { "$($latest.Name) is below the required minimum $min (needed for /jsonAnalysis)" }
	          else          { "vcperf is not installed" }
	Write-Error "$reason and the vcperf feed could not be reached.`n$nugetOutput"
	exit 1
}
