# F1TENTH Research Archive

This directory stores the weekly research record in a predictable, date-first format.

## Naming convention

| Artifact | File name |
| :--- | :--- |
| Readable technical journal | `YYYY-MM-DD-research-journal.md` |
| Original submitted journal | `YYYY-MM-DD-research-journal.pdf` |
| Exact repository change set | `YYYY-MM-DD-code-diff.patch` |

PDF names use the date printed in the submitted journal. Markdown technical notes and patch
files keep the date on which their repository record was prepared. A technical note may therefore
carry a slightly later date than the PDF for the same weekly cycle.

## Journal index

| Report date | Research Journal | Code diff | Main focus |
| :--- | :--- | :--- | :--- |
| **2026-10-01** | [PDF](2026-10-01-research-journal.pdf) | [Integration patch](2026-10-04-integration-code-diff.patch) | Initial VESC IMU and LiDAR-Cartographer integration |
| **2026-10-08** | [PDF](2026-10-08-research-journal.pdf) · [Technical note (Oct 10)](2026-10-10-research-journal.md) | [Patch (Oct 10)](2026-10-10-code-diff.patch) | VESC telemetry, low-speed odometry visibility, and the calibration plan |
| **2026-10-15** | [PDF](2026-10-15-research-journal.pdf) · [Technical note](2026-10-15-research-journal.md) | [Patch](2026-10-15-code-diff.patch) | Cartographer motion estimator and low-speed filter tuning |
| **2026-10-23** | [PDF](2026-10-23-research-journal.pdf) · [Technical note](2026-10-23-research-journal.md) | [Patch](2026-10-23-code-diff.patch) | Powered validation, signed forward speed, and the VESC calibration plan |

The October 4 patch predates the weekly naming convention and is retained as the integration
baseline associated with the October 1 journal.
