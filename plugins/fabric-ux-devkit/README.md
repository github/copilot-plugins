# Fabric UX Devkit

AI-powered tooling for repos that consume [Fabric UX](https://github.com/microsoft/fabric-ux) web components. Includes agents and skills that help LLMs find real Fabric components, assess parity against design specs, and implement UI code — all backed by evidence from installed packages.

> Source: [`brianchristopherbrady/fabric-ux-copilot-plugins`](https://github.com/brianchristopherbrady/fabric-ux-copilot-plugins)

## What it does

Fabric UX Devkit grounds AI assistance in the actual Fabric component catalog, ensuring LLMs use real APIs rather than hallucinated ones. It enables agents to:

| Capability | Description |
| --- | --- |
| **Parity analysis** | Compare a Figma spec or engineering spec against the Fabric component catalog |
| **Component lookup** | Retrieve verified React and Angular usage examples for any Fabric component |
| **Spec-to-code** | Translate an approved design spec into repo-compliant UI code |
| **Gap identification** | Classify component gaps and file feature requests upstream |

## Agent

### `fabric-ux-developer`

Orchestration agent for consumer-repo Fabric UX parity analysis and implementation. Handles design review, parity assessment, report generation, and code implementation across React, Angular, and Web Component framework lanes.

## Skills

| Skill | Description |
| --- | --- |
| **parity-analysis** | Spec-to-catalog parity assessment with environment baseline checks and report generation |
| **react-examples** | Verified React usage examples for every Fabric component |
| **angular-examples** | Verified Angular usage examples for every Fabric component |
| **figma-api** | Figma design extraction for node hierarchy, screenshots, and visual properties |
| **figma-spec-review** | Design-node triage into implement-now, future, and reference-only |
| **figma-to-code** | Translates an approved Figma spec + parity report into repo-compliant UI code |
| **file-fabric-issue** | Files feature requests and bug reports as Azure DevOps work items |
| **feature-switches** | Feature switch discovery and local enablement in PowerBI clients |

## Framework lanes

| Framework | Wrapper package | Evidence source |
| --- | --- | --- |
| React | `@fabric-msft/fabric-react` | + `@fabric-msft/fabric-web` |
| Angular | `@fabric-msft/fabric-angular` | + `@fabric-msft/fabric-web` |
| Web Components | — | `@fabric-msft/fabric-web` |

## License

[MIT](../../LICENSE)
