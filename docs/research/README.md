# F1TENTH Research Archive

This directory stores the weekly research record in a predictable, date-first format.

## Naming convention

| Artifact | File name |
| :--- | :--- |
| Readable technical journal | `YYYY-MM-DD-research-journal.md` |
| Original submitted journal | `YYYY-MM-DD-research-journal.pdf` |
| Exact repository change set | `YYYY-MM-DD-code-diff.patch` |

The date is the report date. When both Markdown and PDF files exist for a date, they describe
the same reporting period: Markdown connects the results to repository files, while PDF
preserves the original submitted document.

## Journal index

| Report date | Research Journal | Code diff | Main focus |
| :--- | :--- | :--- | :--- |
| **2026-10-01** | [PDF](2026-10-01-research-journal.pdf) | [Integration patch](2026-10-04-integration-code-diff.patch) | Initial VESC IMU and LiDAR-Cartographer integration |
| **2026-10-10** | [Markdown](2026-10-10-research-journal.md) | [Patch](2026-10-10-code-diff.patch) | ROS-unit IMU, TF, LiDAR frequency, odometry deadband, and USB identification |
| **2026-10-15** | [Markdown](2026-10-15-research-journal.md) · [PDF](2026-10-15-research-journal.pdf) | [Patch](2026-10-15-code-diff.patch) | Cartographer motion estimator and low-speed filter tuning |
| **2026-10-23** | [Markdown](2026-10-23-research-journal.md) · [PDF](2026-10-23-research-journal.pdf) | [Patch](2026-10-23-code-diff.patch) | Powered validation, signed forward speed, and the VESC calibration plan |

The October 4 patch predates the weekly naming convention and is retained as the integration
baseline associated with the October 1 journal.
