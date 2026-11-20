<#
.SYNOPSIS
	userPromptSubmitted hook for the build-perf-cpp plugin: refresh the correlation id.

.DESCRIPTION
	Writes a fresh GUID to %LOCALAPPDATA%\vcperf\correlation-id on every prompt
	submission so the build-performance-analysis skill can tie traces, JSON
	reports, and build measurements to a single session. The id is written
	atomically (temp file + move) and nothing is written outside
	%LOCALAPPDATA%\vcperf.
#>

$dir = Join-Path $env:LOCALAPPDATA 'vcperf'
New-Item -Path $dir -ItemType Directory -Force | Out-Null

$file = Join-Path $dir 'correlation-id'
$id = [guid]::NewGuid().ToString()
[IO.File]::WriteAllText("$file.tmp", $id, [Text.Encoding]::ASCII)
Move-Item -Path "$file.tmp" -Destination $file -Force
