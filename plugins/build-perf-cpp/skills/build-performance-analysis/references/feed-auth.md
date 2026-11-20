# vcperf Feed Authentication

This is a sub-procedure of the build-performance-analysis skill. Follow it only
when the main skill's resolution block leaves `$vcperf` empty.

## When to use

Use this when `$vcperf` is empty after running the resolution block in the main
skill. Do not run it before the sessionStart hook completes. If `nuget` is
missing or the feed needs first-time auth, the hook fails and this procedure
takes over.

## Steps

### 1. Resolve nuget

```powershell
$nuget = (Get-Command nuget -ErrorAction SilentlyContinue).Source
```

If `$nuget` resolves here, skip to **Install vcperf**.
If `$nuget` is empty, continue to the next step.

### 2. Ask the user before installing nuget (REQUIRED)
If `$nuget` is empty, you MUST get explicit consent before installing.
**Use the `ask_user` tool — never just print prompt text in chat.**

```
ask_user(
  question = "The NuGet CLI was not found. Can I install it with winget (winget install Microsoft.NuGet)?",
  choices  = ["Yes (Recommended)", "No"]
)
```

If the user answers **No**, stop and report that vcperf cannot be installed
without nuget. Suggest installing it manually (it also ships with Visual
Studio) and ensuring it is on PATH. Do NOT fall through to the next step.

### 3. Install nuget with winget

```powershell
winget install --id Microsoft.NuGet --source winget --accept-source-agreements --accept-package-agreements
$nuget = (Get-Command nuget -ErrorAction SilentlyContinue).Source
if (-not $nuget) { $nuget = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\nuget.exe' }
```

If `$nuget` is still empty after this, the install failed — report it and stop;
do not retry without user direction.

### 4. Install vcperf

```powershell
$installDir = Join-Path $env:LOCALAPPDATA 'vcperf\build-perf-cpp'
$feed = 'https://pkgs.dev.azure.com/azure-public/VisualCpp/_packaging/cpp_PublicPackages/nuget/v3/index.json'
& $nuget install Microsoft.Cpp.vcperf -Source $feed -OutputDirectory $installDir
```

The user may see a browser or device-code prompt for authentication — that is expected.

### 5. Re-resolve vcperf

Re-run the resolution block from the main skill's "Which vcperf.exe" section.
If `$vcperf` is still empty, report the error and stop — do not proceed with
tracing or analysis without a confirmed binary.

## Troubleshooting

- **401 or auth error**: The vcperf feed may require network access. Ask
  the user to check connectivity and retry.
- **`nuget` install fails**: If winget or that URL is blocked, ask the
  user to install NuGet manually (it also ships with Visual Studio) and ensure
  it is on PATH.
- **"Unable to load the service index"**: Check network connectivity.
