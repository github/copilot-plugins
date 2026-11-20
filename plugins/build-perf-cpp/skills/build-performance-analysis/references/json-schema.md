# JSON Analysis Output Schema

This document describes every field in the JSON file produced by vcperf when using the /jsonAnalysis flag.

## Top-Level Structure

```json
{
  "BuildDurationMs": <number>,
  "IncludedFiles":   [ ... ],
  "Functions":       [ ... ],
  "Templates":       [ ... ],
  "IncludeTree":     [ ... ]
}
```

- **BuildDurationMs** — Total build wall-clock duration in milliseconds.

---

## IncludedFiles

Top 15 most expensive header files sorted by WCTR. Aggregated across all translation
units: the same header included from many `.cpp` files appears as one entry with a
combined count and WCTR.

```json
{
  "filePath": "C:\\...\\windows.h",
  "wallClockMillisecondTimeResponsibility": 21425,
  "wctrPercentage": 0.120,
  "count": 893,
  "projectFullPath": "C:\\...\\MyProject.vcxproj",
  "component": "C:\\...\\main.cpp"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `filePath` | string | Absolute path to the included header |
| `wallClockMillisecondTimeResponsibility` | number | WCTR in **milliseconds** |
| `wctrPercentage` | number | WCTR / BuildDurationMs |
| `count` | number | Total include count across all translation units |
| `projectFullPath` | string | Full path to the `.vcxproj` (empty if unavailable) |
| `component` | string | Translation unit that included this header |

---

## Functions

Top 15 most expensive functions sorted by WCTR. Captures code generation cost during
the back-end (linker/codegen) phase.

```json
{
  "functionName": "void __cdecl MyFunc(int)",
  "wallClockMillisecondTimeResponsibility": 500,
  "filePath": "C:\\...\\myfile.cpp",
  "forceinlineSize": 1024,
  "wctrPercentage": 0.003,
  "projectName": "MyProject"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `functionName` | string | Decorated function name |
| `wallClockMillisecondTimeResponsibility` | number | WCTR in **milliseconds** |
| `filePath` | string | Source file containing the function |
| `forceinlineSize` | number | Aggregate code size from `__forceinline` callees |
| `wctrPercentage` | number | WCTR / BuildDurationMs |
| `projectName` | string | Project name |

---

## Templates

Top 15 most expensive primary templates sorted by WCTR. Requires `/templates` flag.
WCTR is calculated using non-overlapping interval merging to avoid double-counting
parallel instantiations.

```json
{
  "templateName": "std::vector<_Ty,_Alloc>",
  "wallClockMicrosecondTimeResponsibility": 4500000,
  "wctrPercentage": 0.025,
  "instantiationCount": 312,
  "instantiationPath": "C:\\...\\main.cpp"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `templateName` | string | Primary template name |
| `wallClockMicrosecondTimeResponsibility` | number | WCTR in **microseconds** |
| `wctrPercentage` | number | WCTR(µs) / BuildDuration(µs) |
| `instantiationCount` | number | Total instantiations of this primary template |
| `instantiationPath` | string | Source file where the first instantiation occurred |

> **Note:** Template WCTR is in microseconds, unlike files and functions which use milliseconds.

---

## IncludeTree

Every C/C++ source file (`.cpp`, `.cxx`, `.cc`, `.c`) with its direct `#include`
dependencies and their wall time. Mirrors the include graph per translation unit.

```json
{
  "filePath": "C:\\...\\MAIN.CPP",
  "component": "C:\\...\\main.cpp",
  "projectName": "MyProject",
  "wallTimeMs": 3070,
  "wctrPercentage": 0.017,
  "directIncludes": [
    {
      "filePath": "C:\\...\\myheader.h",
      "wallTimeMs": 1818,
      "wctrPercentage": 0.010
    }
  ]
}
```

### Source file entry

| Field | Type | Description |
|-------|------|-------------|
| `filePath` | string | Path to the source file |
| `component` | string | Translation unit path |
| `projectName` | string | Project name |
| `wallTimeMs` | number | Total wall time in milliseconds |
| `wctrPercentage` | number | WCTR / BuildDurationMs |
| `directIncludes` | array | List of directly included files |

### Direct include entry

| Field | Type | Description |
|-------|------|-------------|
| `filePath` | string | Path to the included file |
| `wallTimeMs` | number | Wall time in milliseconds |
| `wctrPercentage` | number | WCTR / BuildDurationMs |
