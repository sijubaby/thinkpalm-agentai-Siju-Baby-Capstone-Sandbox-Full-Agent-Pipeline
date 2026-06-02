# 8-minute demo script (Maritime / Python)

| Time | Content |
|------|---------|
| 0:00–0:45 | Problem: ThinkPalm maritime QA — manual BDD + Playwright is slow; compliance gaps are costly |
| 0:45–1:30 | Architecture diagram: 3 agents, memory (`data/runs/`), 4 tools |
| 1:30–3:00 | **UI:** `qa-agent ui` → Run pipeline (or CLI: `qa-agent run …`) |
| 3:00–4:30 | Open `generated.feature` — show embarkation block scenario |
| 4:30–5:30 | `pytest tests/e2e -v` — one passing Playwright test |
| 5:30–7:00 | Open `coverage-report.html` — highlight compliance flag on alert schedule / edge cases |
| 7:00–8:00 | Run AIS domain or show `data/samples/ais-*.md`; GitHub link |

## Commands to record

```powershell
cd maritime-qa-agent
.\.venv\Scripts\activate
qa-agent run -s data/samples/crew-certification-expiry-alerts.md -d crew-cert -o data/out/demo
start data\out\demo\coverage-report.html
pytest tests/e2e -v -k test_block_embarkation
```
