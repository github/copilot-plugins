# Build Performance for C++

Analyze MSVC build performance with `vcperf.exe` and ETL traces from GitHub
Copilot CLI.

## Features

- Captures diagnostic traces for MSVC builds
- Generates structured `/jsonAnalysis` reports
- Identifies expensive headers, functions, and template instantiations
- Recommends targeted build-performance improvements
- Measures clean and iterative builds before and after changes

## Requirements

- Windows with the MSVC toolchain
- NuGet CLI (`nuget.exe`) on `PATH`
- Administrator privileges, or a one-time `vcperf /grantusercontrol`
- Network access to the public Visual C++ package feed

The session-start hook installs or updates the newest published
`Microsoft.Cpp.vcperf` package under
`%LOCALAPPDATA%\vcperf\build-perf-cpp`.

## Install

The `copilot-plugins` marketplace is registered by default in Copilot CLI:

```powershell
copilot plugin install build-perf-cpp@copilot-plugins
```

## Use

Start Copilot CLI in an MSVC project and ask:

```text
Improve the build performance of this project.
```

The `build-performance-analysis` skill captures a trace, ranks build
bottlenecks, recommends changes, and compares uninstrumented before-and-after
build measurements.

## Hooks

- `sessionStart` installs or updates `vcperf.exe`.
- `userPromptSubmitted` creates a correlation identifier for trace artifacts.

Both hooks operate locally and write only beneath `%LOCALAPPDATA%\vcperf`.

## Contributors

- Ion Todirel
- Eve Silfanus
