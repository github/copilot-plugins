---
name: build-performance-analysis
description: >
  Analyze C++ build performance using vcperf.exe and ETL traces. Use this skill
  when the user wants to profile a build, understand compile bottlenecks, identify
  expensive headers or templates, generate JSON analysis reports, or interpret
  vcperf output. Covers tracing workflows, the /jsonAnalysis flag, reading
  the resulting JSON schema, and actionable remediation strategies for each
  bottleneck category.
compatibility: Windows with MSVC toolchain. Requires administrator privileges for default tracing.
---

# Build Performance Analysis with vcperf.exe

## Execution order

A single **workflow**, always run in order.

### Workflow — always run, in order

**Treat each session as independent.** Re-capture traces, JSON analysis, and baseline measurements fresh each session instead of reusing data from a previous session — the one-time trace-permission grant persists.

1. [Prerequisites: Trace Permission](#prerequisites-trace-permission) — grant ETW rights. Run **before** any workspace exploration (project enumeration, file listing, code search).
2. [Core Workflow](#core-workflow) + [The /jsonAnalysis Flag](#the-jsonanalysis-flag)
3. [Baseline Measurement](#baseline-measurement) — 5 uninstrumented clean rebuilds of the **pre-change** state; average for a stable baseline. **Make no code or project edits during this step**.
4. [Remediation Strategies](#remediation-strategies) — the **first** step where you edit anything; apply changes informed by Steps 2–3.
5. [Measuring Final Performance Improvement](#measuring-final-performance-improvement) — 5 uninstrumented clean rebuilds of the post-change state; compare against the baseline. If a PCH or template change shows a neutral or regressed delta, also run [Iterative Build Measurement](#iterative-build-measurement).

## Which vcperf.exe executable should I use?

The `sessionStart` hook installs `vcperf.exe` under `%LOCALAPPDATA%\vcperf\build-perf-cpp` (multiple versions may coexist). Resolve the **newest** version once and reuse it:

```powershell
$vcperfPkg = Get-ChildItem "$env:LOCALAPPDATA\vcperf\build-perf-cpp" -Directory -Filter 'Microsoft.Cpp.vcperf.*' -ErrorAction SilentlyContinue | Sort-Object { ($_.Name -replace '^Microsoft\.Cpp\.vcperf\.', '' -split '\.' | ForEach-Object { ([long]$_).ToString().PadLeft(20, '0') }) -join '.' } -Descending | Select-Object -First 1
$vcperf = if ($vcperfPkg) { (Get-ChildItem $vcperfPkg.FullName -Recurse -Filter vcperf.exe | Where-Object DirectoryName -like '*\x64' | Select-Object -First 1).FullName }
```

**Authentication**: If `$vcperf` resolves empty, read `references/feed-auth.md` and follow it before proceeding.

### Invocation rule (read before running any vcperf command)

Every `vcperf` command below runs the resolved `$vcperf` path directly in PowerShell (`& $vcperf ...`). Both rules are mandatory:

1. **Use the absolute `$vcperf` path, never a bare `vcperf`.** Bare `vcperf` resolves off `PATH` to the older Visual-Studio-bundled copy (may lack `/jsonAnalysis`), not the one under `%LOCALAPPDATA%\vcperf\build-perf-cpp`.
2. **Judge success by the output file, not `$LASTEXITCODE`.** PowerShell's `& $vcperf` can surface an internal COM `HRESULT` (e.g. `0x80040013`) in `$LASTEXITCODE` and render output as blank lines, so a run that actually succeeded can look failed. After a `/stop` or `/stopnoanalyze`, confirm the expected `.etl`/`.json` file was written (`Test-Path`) instead of trusting the exit code.

The command blocks in [Prerequisites](#prerequisites-trace-permission) and [Core Workflow](#core-workflow) below apply both rules — follow their exact form.

## What is vcperf?

vcperf.exe captures and analyzes C++ build traces using the C++ Build Insights SDK. It records ETW events during MSVC compilations and produces either ETL files (for Windows Performance Analyzer) or structured JSON reports.

## Prerequisites: Trace Permission

`vcperf /start` writes ETW providers that require **either**:

- the invoking process to be **elevated (Administrator)**, OR
- a one-time **`vcperf /grantusercontrol`** run elevated for the current user — after which non-admin invocations may use `/start /noadmin` (reduced data: no CPU sampling).

The CLI agent runs unelevated and **must solve this itself** — do not ask the user to "open an elevated prompt and run X by hand".

Run on first use. Once Step 4 verifies the grant, Step 4b persists a per-user marker file so **future sessions skip Trace Permission Steps 2–4 entirely**. Within a session, also cache the Step 1 result in working memory. **Skip entirely for `vcperf /analyze` and `vcperf /stop` against an existing trace** — only `/start` needs the grant.


### Step 1 — Check whether rights already exist

Two signals; either is sufficient. **Run Check A first; skip Check B if A is true.**

**Check A — process is elevated:**

```powershell
$isAdmin = ([Security.Principal.WindowsPrincipal]::new(
    [Security.Principal.WindowsIdentity]::GetCurrent())
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
```

If `$isAdmin` is `$true` → skip to Step 5.

**Check B — agent-persisted grant marker** (only when Check A is false):

```powershell
$grantMarker = Join-Path $env:LOCALAPPDATA 'vcperf\grant-verified'
$hasGrantMarker = Test-Path -LiteralPath $grantMarker -PathType Leaf

```

If `$hasGrantMarker` is `$true`, the agent already granted and verified rights in a previous session — proceed without re-prompting.

**If Check A OR Check B is true → you have rights. Skip to Step 5.**

### Step 2 — Ask the user before triggering UAC (REQUIRED)

If neither check is true, you MUST get explicit consent before launching an elevated process. **Use the `ask_user` tool — never just print prompt text in chat.**

```
ask_user(
  question = "vcperf needs additional permissions to execute a trace. May I run a one-time elevated `vcperf /grantusercontrol`? A UAC prompt will appear.",
  choices  = ["Yes (Recommended)", "No"]
)
```

If the user answers **No**, stop the workflow. Report that vcperf cannot run without trace permission and let the user decide how to proceed. Do NOT fall through to Step 3, do not retry, and do not silently downgrade to a non-vcperf measurement.

### Step 3 — Grant rights elevated

Launch an elevated PowerShell that runs `vcperf /grantusercontrol` and wait for it. The grant produces no output artifact, so Step 4 verifies it functionally:

```powershell
# $vcperf must already hold the absolute path (see resolution block above).
# /grantusercontrol writes no output file, so Step 4 verifies it functionally;
# we don't depend on vcperf's exit code here (see Invocation rule).
try {
    Start-Process powershell.exe `
        -ArgumentList '-NoProfile','-Command',"& '$vcperf' /grantusercontrol" `
        -Verb RunAs -Wait
    $grantCancelled = $false
} catch [System.ComponentModel.Win32Exception] {
    if ($_.Exception.NativeErrorCode -eq 1223) {
        # Win32 error 1223 = ERROR_CANCELLED — user dismissed the UAC prompt.
        $grantCancelled = $true
    } else {
        throw
    }
}
$grantCancelled
```

- A UAC dialog will appear. If the user cancels it, `Start-Process -Verb RunAs` throws `Win32Exception` with `NativeErrorCode = 1223` — treat that as "user declined" and stop (same outcome as a "No" in Step 2).
- Otherwise the elevated grant ran. Its exit code is not reliable (see Invocation rule), so **Step 4 is the authoritative check** that the grant actually worked — proceed there.

### Step 4 — Verify the grant worked

Do not trust Step 3 alone — run a functional probe. Use `/stopnoanalyze` (not `/stop`); the probe only needs to prove `/start /noadmin` succeeded, and `/stop` would waste seconds analyzing an empty session.

```powershell
$probe   = 'PermProbe_' + [guid]::NewGuid().ToString('N').Substring(0,8)
$probeEtl = Join-Path $env:TEMP "$probe.etl"
Remove-Item $probeEtl -ErrorAction SilentlyContinue
# Success signal is whether the probe ETL is produced, not $LASTEXITCODE
# (see Invocation rule). A working /start + /stopnoanalyze writes the ETL;
# if /start was denied, no ETL appears.
$startOutput = (& $vcperf /start /noadmin $probe *>&1 | Out-String).Trim()
$stopOutput = (& $vcperf /stopnoanalyze $probe $probeEtl *>&1 | Out-String).Trim()
$started = Test-Path $probeEtl
if (-not $started) {
    $probeOutput = @($startOutput, $stopOutput) | Where-Object { $_ }
    Write-Error ("vcperf permission probe failed.`n" + ($probeOutput -join "`n"))
}
Remove-Item $probeEtl -ErrorAction SilentlyContinue
$started
```

If `$started` is `$true`, the grant is verified — proceed. If `$false`, the grant did not take effect — surface the failure with the vcperf output and stop. Do not silently retry. **Do NOT run Step 4b on a failed verify.**

### Step 4b — Persist the verified grant (so future sessions skip Steps 2–4)

Run only **after** Step 4 returned `$started = $true`. Write the per-user **marker file** that Check B reads:

```powershell
$grantMarker = Join-Path $env:LOCALAPPDATA 'vcperf\grant-verified'
New-Item -Path (Split-Path $grantMarker -Parent) -ItemType Directory -Force | Out-Null
$payload = @{ grantedUtc = (Get-Date).ToUniversalTime().ToString('o'); vcperf = $vcperf } | ConvertTo-Json -Compress
[IO.File]::WriteAllText("$grantMarker.tmp", $payload, [Text.Encoding]::UTF8)

Move-Item -LiteralPath "$grantMarker.tmp" -Destination $grantMarker -Force
```

- Check presence of marker file to determine if grant is persisted.
- On every subsequent session, Check B returns `$true` and the agent skips straight to Step 5.

### Step 5 — Invoke vcperf with the right flag

When starting the tracing session:

- **always** pass `/noadmin` to `vcperf /start`, or the start will fail with a privilege error.
- **Stale-grant recovery.** If `/start /noadmin` fails with a privilege error while Check B was `$true`, the cached grant is stale (the underlying ETW grant was revoked outside the agent). Recover by running Steps 2–4 directly — **skip Step 1**.


## Core Workflow

There are three phases: **start** a trace, **build** your project, then **stop** and **analyze** to produce results.

> Below, `vcperf` is shorthand for the resolved `$vcperf` absolute path run directly in PowerShell (`& $vcperf ...`), per the [Invocation rule](#invocation-rule-read-before-running-any-vcperf-command). Never run a bare `vcperf` (it hits the VS-bundled copy on `PATH`), and judge success by the output file rather than `$LASTEXITCODE`.

### 1. Start a tracing session

```
vcperf /start [/noadmin] [/nocpusampling] [/level1 | /level2 | /level3] <sessionName>
```

| Flag | Purpose |
|------|---------|
| `/noadmin` | Run without admin (less data) |
| `/nocpusampling` | Skip CPU sampling |
| `/level1` | Basic events |
| `/level2` | Adds additional detail |
| `/level3` | Maximum detail, includes template instantiation data |

Use `/level3` when you plan to analyze templates.

### 2. Build your project

Run your normal build command while the trace is active. Any MSVC-driven build works — MSBuild, CMake (Ninja or MSBuild generator), or direct `cl.exe`. The *compiler* must be MSVC; the *build driver* is your choice.

When building solution files, look for either `.sln` or `.slnx`.

#### Build configuration matters (Debug vs Release)

vcperf only reports work the compiler actually performs. **Debug** builds skip most optimizer passes, so the `Functions` section of the JSON output will be sparse or empty — you will not see backend codegen, inlining, or optimization hotspots. Frontend phases (`IncludedFiles`, `Templates`) are still captured normally because parsing and template instantiation happen regardless of configuration.

For meaningful function-level analysis, build in **Release** (or another optimized configuration such as `RelWithDebInfo`). As a rule, profile the configuration you intend to ship; before choosing Debug, confirm with the user that frontend-only data is enough for their question, and call out the missing `Functions` data in your report.

### 3. Stop and analyze

```
vcperf /stop [/templates] <sessionName> output.etl
vcperf /stop [/templates] <sessionName> output.etl /jsonAnalysis output.json
vcperf /stop [/templates] <sessionName> /timetrace output.json
```

Or capture raw first, then analyze offline:

```
vcperf /stopnoanalyze <sessionName> raw.etl
vcperf /analyze [/templates] raw.etl output.etl /jsonAnalysis output.json
```

### 4. Avoid timing gaps — run start/build/stop as one shell command

`vcperf` records ETW events from `/start` until `/stop`. **Any wall-clock gap between `/start`, the build, and `/stop` is captured as noise** — model thinking, tool-call round-trips, prompts, and shell startup all inflate `BuildDurationMs` and can shift hotspot rankings.

From a CLI agent or any interactive workflow, **chain `/start → build → /stop` into a single shell command**. Do not issue them as three separate tool calls — the latency between calls (often several seconds each) contaminates the trace.

**PowerShell with MSBuild (single invocation — recommended):**
```powershell
# $vcperf holds the absolute path resolved earlier. Run as one scriptblock so
# /start -> build -> /stop execute back-to-back with no timing gaps. Judge trace
# success by the output files (Test-Path), not $LASTEXITCODE (see Invocation rule).

$buildExit = & {
    & $vcperf /start /noadmin /level3 MySession | Out-Host
    msbuild Project.sln /m /t:Rebuild /p:Configuration=Release | Out-Host
    $exitCode = $LASTEXITCODE
    & $vcperf /stop /templates MySession out.etl /jsonAnalysis out.json | Out-Host
    $exitCode
}
$traceOk = (Test-Path out.etl) -and (Test-Path out.json)
```

**PowerShell with CMake (single invocation):**
```powershell
$buildExit = & {
    & $vcperf /start /noadmin /level3 MySession | Out-Host
    cmake --build build --target clean | Out-Host
    cmake --build build --parallel | Out-Host
    $exitCode = $LASTEXITCODE
    & $vcperf /stop /templates MySession out.etl /jsonAnalysis out.json | Out-Host
    $exitCode
}
$traceOk = (Test-Path out.etl) -and (Test-Path out.json)
```
`$buildExit` is the build tool's own exit code (reliable — an ordinary process), telling you whether the build succeeded. `$traceOk` confirms vcperf actually produced the trace. The `;` sequence never short-circuits, so `/stop` always runs even if the build fails.

**cmd.exe alternative** (if you prefer `&&` short-circuit semantics; substitute the full path for `%VCPERF%`):
```cmd
"%VCPERF%" /start /noadmin /level3 MySession && cmake --build build --target clean && cmake --build build --parallel && "%VCPERF%" /stop /templates MySession out.etl /jsonAnalysis out.json
```
`&&` skips `/stop` if the build fails; replace the `&&` before the final `"%VCPERF%" /stop` with `&` to emit the trace anyway.

The same rule applies to incremental measurements (see [Iterative Build Measurement](#iterative-build-measurement)): the touch step may be a separate command, but `/start → build → /stop` must be one chained invocation.

## The /jsonAnalysis Flag

Produces a structured JSON report alongside the ETL output.

**Syntax:** `/jsonAnalysis <path>.json` — must appear **after** the ETL output path.

**Constraints:**
- Cannot be combined with `/timetrace` (mutually exclusive).
- Pair with `/templates` to include template data.

**Example:**
```
vcperf /stop /templates MyBuild output.etl /jsonAnalysis analysis.json
```

## JSON Output Schema

See [references/json-schema.md](references/json-schema.md) for the full field-by-field schema of the JSON analysis output, including `IncludedFiles`, `Functions`, `Templates`, and `IncludeTree` sections.

---

## Baseline Measurement

Establish a baseline **before** applying the candidate change. A single build measurement is noisy — file system caches, antivirus, background processes, and thermal throttling all introduce variance, so always run a 5-build sample.

**Do not run vcperf during these builds.** The diagnostic trace that tells you *what* to change is captured separately via the [Core Workflow](#core-workflow); baseline and post-change timing builds are plain, uninstrumented wall-clock builds. vcperf's ETW instrumentation adds overhead that would contaminate timing comparisons.

**Make no changes to the project while measuring the baseline.** No modifications to the project until all baseline builds complete.

### Procedure

1. **Run 5 builds** of the target as a full clean rebuild (clean before every build), **without vcperf**. Every run uses identical configuration, platform, build parallelism (e.g. MSBuild `/m`, CMake `--parallel`, ninja's default `-j`), and machine state (plugged in, no background load).
2. **Average the 5 builds** for a stable baseline.
3. Record the baseline average and standard deviation. Compare post-change measurements against this baseline using the same methodology (5 uninstrumented builds).
4. **Measure wall-clock time** of each build (e.g. `Measure-Command { msbuild ... }` or `Measure-Command { cmake --build build }`, or the build driver's own elapsed time). Record in **seconds** — all measurements, deltas, and statistics in this skill are in seconds, never milliseconds. Do **not** use `BuildDurationMs` from a vcperf JSON; that field comes from an instrumented trace and is not the metric you are optimizing.
5. **Keep fixed between runs:** build parallelism, build-server / node reuse, configuration, platform, power state, source/output state. Do not change any source files or project settings during baseline measurement.

## Iterative Build Measurement
Use this only **after one full rebuild**.

### Procedure overview

An **A/B comparison of two incremental builds** with an identical workload:

- **A:** candidate changes applied, the same set of TUs forced dirty
- **B:** candidate changes reverted, the same set of TUs forced dirty

Both runs must mark the same files dirty and start from a `.obj` state matching the source they are about to compile.

### Step 1 — Pick the TU files to touch

Combine two signals and **prefer their intersection** (fall back to whichever is non-empty):

Reuse the `/jsonAnalysis` output from [Core Workflow](#core-workflow). After applying [the selection rules](#remediation-strategies), take the top expensive headers in `IncludedFiles`
- **Frequently-changed TUs from git churn.** Use only commits **before the branch fork-point** (see "Git History Rules" below):
  ```powershell
  $forkPoint = git merge-base HEAD origin/main
  git log --name-only --pretty=format: $forkPoint -- '*.cpp' '*.cxx' '*.cc' '*.c' |
      Where-Object { $_ } |
      Group-Object | Sort-Object Count -Descending |
      Select-Object -First 50
  ```

### Step 2 — Touch (do not edit) the chosen files

Update last-write-time only:

```powershell
$touchTime = (Get-Date).ToUniversalTime()
foreach ($file in $tuFiles) {
    if (Test-Path $file) { (Get-Item $file).LastWriteTimeUtc = $touchTime }
}
```

### Step 3 — Pair-and-alternate, 5 iterations each side

Measured builds are **plain, uninstrumented, non-vcperf** wall-clock builds (`Measure-Command { msbuild ... }` / `Measure-Command { cmake --build build }`), recorded in **seconds**.

For each iteration:

1. Ensure candidate changes are **applied** (`git stash pop` or be on the change branch); run a regular build to settle `.obj` state; touch the chosen TUs; run an uninstrumented incremental build. Record as **A** (with changes).
2. **Revert** candidate changes (`git stash` or switch to base branch); run a regular build to settle `.obj` state; touch the same TUs; run an uninstrumented incremental build. Record as **B** (baseline).

The "settle `.obj` state" build after each switch is mandatory — skip it and A and B compile different amounts of code. **Alternate** A and B per iteration (not 5 As then 5 Bs) to average out warm-cache and thermal effects.

### Step 4 — Compare and report

Meaningful improvement is `A_avg < B_avg - B_stddev` (same rule as the rebuild baseline). Report all times in **seconds** with the standard deviation in its own column (no `mean ± stddev` shorthand):

| Variant | Mean (s) | StdDev (s) |
|---|---|---|
| A (with changes) | ... | ... |
| B (baseline) | ... | ... |

Also report the number of TUs touched, `delta_s = B_avg - A_avg` (positive = improvement), and `delta_pct = delta_s / B_avg * 100`.

## Git History Rules

**CRITICAL:** Do not use git history (log, blame, diff) for commits **after** the branch fork-point (merge-base with the base branch). Build performance analysis evaluates the current state of the code — post-fork-point history can bias optimization decisions.

You MAY use git history for commits **before** the fork-point to understand:
- When a header was introduced or significantly changed.
- Historical context for why a particular include structure exists.
- Whether a PCH previously existed and was removed.

## Remediation Strategies

After producing a JSON analysis report and **applying the selection rules above**, use the strategies below to fix each category. Always **re-profile after each change** to verify improvement and catch regressions.

### Expensive Included Files (`IncludedFiles`)

Headers with high WCTR and high include counts are the highest-leverage targets. A header included in N translation units has its parse cost multiplied N times.

#### Strategy 1 — Use or create a precompiled header (PCH)
A PCH parses expensive headers once and reuses the result across all translation
units. This is the single most effective technique for headers that are both
expensive and widely included.

**When to use:**
- Headers with high WCTR, high include count, and low change frequency.
- STL headers (`<string>`, `<vector>`, `<map>`, `<memory>`, etc.) are ideal
  because they never change.
- Third-party library headers (GLM, SDL, fmt, etc.) are excellent candidates.
- Stable project headers that are included in many TUs but rarely modified.

**How to evaluate project headers for PCH inclusion:**
1. Check the header's WCTR and include count from the JSON report.
2. Check change frequency: `git log --oneline --since="1 year ago" -- path/to/header.hpp`

**PCH header selection tiers:**
| Tier | Type | Example | Risk |
|------|------|---------|------|
| 1 (always safe) | STL headers | `<string>`, `<vector>` | None — never change |
| 2 (safe) | Third-party | `<glm/glm.hpp>`, `<SDL.h>` | Low — change only on dependency upgrade |
| 3 (evaluate) | Stable project | Core type headers, rendering API | Medium — check git history first |
| 4 (avoid) | Volatile project | Actively developed feature headers | High — triggers frequent full rebuilds |

If the PCH change already shows a statistically significant clean-rebuild improvement, **the change is validated — do not run the iterative workflow.**

#### Strategy 2 — Use forward declarations

If a header only uses pointers or references to a type, it does not need the full definition — a forward declaration suffices.

1. In headers, replace `#include "foo.hpp"` with `class Foo;` when only `Foo*`, `Foo&`, or `std::unique_ptr<Foo>` are used.
2. Move `#include "foo.hpp"` to the `.cpp` file where the full definition is needed.
3. Consider a project `fwd.hpp` that collects common forward declarations for widely-used types.

#### Strategy 3 — Flatten include chains

Deeply nested include chains amplify costs. If header A includes B which includes C which includes D, every file that includes A pays for all four.

1. Use `IncludeTree` to identify deep chains.
2. Audit intermediate headers — do they really need everything they include?
3. Break long chains by removing unnecessary intermediate includes; have consumers include what they need directly.

---

### Expensive Functions (`Functions`)

Functions with high WCTR are expensive during the back-end code generation (compilation/linking) phase.

#### Strategy 1 — Reduce `__forceinline` and excessive inlining

The `forceinlineSize` field reveals how much code is inlined into each function. The larger this value relative to other entries in the post-filter top-15, the more aggressive inlining has bloated the function's body.

1. Compare `forceinlineSize` across the top-15 entries — the entries at the top of the weighted ranking are the ones whose inline bloat is paying off the least.
2. Find functions or methods marked `__forceinline`, `__attribute__((always_inline))`, or defined in headers as `inline` that are called from the expensive function. **Use the demangled `functionName`** — the raw JSON name is decorated and will not match source-text grep.
3. Move large inline function bodies from headers to `.cpp` files (see Strategy 3 below).
4. Replace `__forceinline` with regular `inline` or no annotation — let the compiler decide. Reserve `__forceinline` for genuinely tiny, hot-path functions.
5. For template-heavy code, consider explicit template instantiation in a `.cpp` file to avoid redundant codegen across TUs.

#### Strategy 2 — Break up large functions

Very large functions are expensive to optimize (register allocation, instruction scheduling, etc.).

1. Identify functions among the post-filter top-15 whose `wallClockMillisecondTimeResponsibility` is large relative to others in the list. The relative ranking is the signal — there is no absolute time cutoff.
2. Extract logically independent sections into separate helper functions.
3. Move cold paths (error handling, logging, rare branches) into separate `__declspec(noinline)` or `[[gnu::noinline]]` functions to reduce optimizer workload on the hot path.
4. **Prefer breaking up before marking `noinline`.** `noinline` is the last-resort hammer.

#### Strategy 3 — Keep the implementation private to the `.cpp` file

A function body defined inside a class declaration (or marked `inline` in a header) is implicitly inline: every TU that includes the header parses the body and instantiates every template it touches, even TUs that never call the function. Moving the body to the `.cpp` file pays each cost exactly once. This matters most when the inline body uses STL algorithms or other heavily templated code — each `#include` of the header re-instantiates those templates.

**Anti-pattern — body defined inline in the header:**

```cpp
// ----- foo.h -----
#include <algorithm>   // ← every consumer of foo.h pays for <algorithm>
#include <string>

class foo
{
    foo(std::string str)
    {
        std::find_if(str.begin(), str.end(), [](char c) { return c == 'ch'; });
        // std::find_if is instantiated in EVERY TU that includes foo.h.
    }
    void bar();
};

// ----- foo.cpp -----
#include "foo.h"
void foo::bar() { }
```

**Refactored — implementation private to `foo.cpp`:**

```cpp
// ----- foo.h -----
#include <string>

class foo
{
    foo(std::string str);   // declaration only
    void bar();
};

// ----- foo.cpp -----
#include "foo.h"
#include <algorithm>   // ← only foo.cpp pays for <algorithm> now

foo::foo(std::string str)
{
    std::find_if(str.begin(), str.end(), [](char c) { return c == 'ch'; });
}

void foo::bar() { }
```

`<algorithm>` and the `std::find_if` instantiation now occur once instead of once per TU. Combine with **Headers — Strategy 2 (forward declarations)** to push more includes from `.h` to `.cpp`.

Apply when an inline header-defined body references heavy templated code (`<algorithm>`, `<regex>`, `<format>`, `<ranges>`, `<filesystem>`, `<chrono>`) and the header is widely included. Skip for trivial accessors and templates themselves (their definitions must stay visible — use explicit instantiation, Strategy 1 step 5).

---

### Expensive Templates (`Templates`)

Templates with high WCTR and high instantiation counts cause the compiler to repeat work across many TUs. Reminder: template WCTR is in **microseconds** (`wallClockMicrosecondTimeResponsibility`); only the top **15** entries are considered.

#### Strategy 1 — Reduce instantiation count

1. Check `instantiationCount` — thousands of instantiations of the same template are a red flag.
2. Identify whether the high count is from a project template or a standard library template (e.g. `std::vector`, `std::unordered_map`).
3. For **project templates**: limit distinct template arguments. Consider type-erased wrappers or base classes to reduce unique instantiations.
4. For **STL templates**: typically unavoidable but mitigated by PCH (see above) since the compiler caches template definitions from precompiled headers.

#### Strategy 2 — Explicit template instantiation

For project templates instantiated with a known, finite set of types:

1. Declare the template as `extern` in the header:
   ```cpp
   // widget.hpp
   template<typename T> class Widget { /* ... */ };
   extern template class Widget<int>;
   extern template class Widget<float>;
   ```
2. Provide explicit instantiations in one `.cpp` file:
   ```cpp
   // widget.cpp
   template class Widget<int>;
   template class Widget<float>;
   ```
3. Each instantiation is now compiled once rather than in every TU that uses it.

#### Strategy 3 — Move template definitions out of headers

1. If a template's implementation is large, keep only the declaration in the header and move the definition to a `.inl` or `.tpp` file included only where needed.
2. For templates used in only a few TUs, move the full definition to a `.cpp` file with explicit instantiations.

#### Strategy 4 — Simplify template metaprogramming

1. Templates with deep recursion or heavy SFINAE/`std::enable_if` are expensive to instantiate.
2. Prefer C++17 `if constexpr` over SFINAE for compile-time branching.
3. Prefer C++20 concepts over complex `std::enable_if` chains.
4. Reduce template nesting depth — flatten helper hierarchies.

---

### General Optimization Checklist

After profiling and before making changes, run through this checklist:

1. **Quick wins (minutes, high impact):**
   - Remove umbrella/catch-all includes from widely-included headers.
   - Create or fix PCH with STL + **Tier-2 third-party umbrella headers** (any heavily-included third-party "include everything" header your project uses). Missing these is a common cause of an under-performing PCH in projects built around third-party umbrella libraries.
   - Add stable, widely-included project headers to the PCH (see Strategy 1's PCH header selection tiers above).

2. **Medium effort (hours, moderate impact):**
   - Add forward declarations to headers that only use pointer/reference types.
   - Move large inline functions from headers to `.cpp` files.
   - Use explicit template instantiation for common specializations.

3. **Larger refactors (days, lower marginal impact):**
   - Split large TUs into smaller files.
   - Flatten deep include chains.
   - Replace heavy template metaprogramming with simpler alternatives.

Always re-profile after each round of changes to measure improvement and confirm no regressions.

---

## Measuring Final Performance Improvement

This section defines **only the post-measurement decision logic and report format**. Measurement procedures live in [Baseline Measurement](#baseline-measurement) and [Iterative Build Measurement](#iterative-build-measurement)

### When to additionally run iterative measurement

After re-running a clean rebuild against the modified project, **skip iterative measurement when the clean rebuild already shows a statistically significant improvement** — it adds 10+ extra timed builds and confirms nothing new.

Otherwise, also run [Iterative Build Measurement](#iterative-build-measurement) when **all** of the following are true:

1. The change added upfront compilation cost — specifically a **PCH** or shared explicit template instantiation.
2. The clean-rebuild result is neutral, regressed, or within `baseline_average ± baseline_stddev`.
3. The change is theoretically sound based on the JSON analysis (e.g., a header used in many TUs was moved into a PCH and *should* amortize across iterative edits).

A change is a **net win** if either the clean-rebuild OR the iterative result is statistically significant and the other is at worst neutral.

### Summary format

**When validation ran**, report all times in seconds with mean and standard deviation in **separate columns** — do not use the `mean ± stddev` shorthand. Include both measurements when iterative ran. If you tried an approach that did not work and switched strategies, briefly state what you tried and why you moved on.

| Measurement | Variant | Mean (s) | StdDev (s) | Delta % |
|---|---|---|---|---|
| Clean rebuild | baseline | 45.2 | 1.8 | |
| Clean rebuild | post | 47.1 | 1.5 | -4.2% (regression) |
| Iterative build | baseline | 8.4 | 0.3 | |
| Iterative build | post | 3.1 | 0.2 | +63.1% (significant) |

Decision: keep change — large iterative win outweighs small rebuild regression.