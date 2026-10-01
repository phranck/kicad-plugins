# Working in this repository

**Commit straight to `main`. No feature branch, no pull request.**

Stated by phranck on 2026-10-01: "mach das ohne branch und pr, direkt auf main". This overrides the general rule that code reaches a remote through a branch and a pull request. One maintainer works here on small, independent plugins, so a pull request adds a step without adding a reviewer.

What does not change is the gate before pushing. There is no CI and no test suite, so the gate is that every touched plugin still compiles and imports, and that a lint run reports nothing the previous commit did not already report.

Each plugin lives in its own folder with its own README and installs on its own, so a change to one never touches another.
