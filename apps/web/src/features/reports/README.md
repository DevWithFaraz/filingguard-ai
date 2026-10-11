# reports

P0: saved-result report and Markdown/HTML download; PDF is P1. T051, T104.

Implemented in the shared saved-results screen, not a duplicate standalone page:
[[apps/web/src/features/analyses/README]]. It downloads authenticated saved backend
Markdown/HTML reports; [[apps/api/src/filingguard/modules/reports/README]] owns
rendering and escaping. A separate PDF export remains P1.
Use shared API types/client from src/lib/api. Display backend statuses faithfully;
do not duplicate legal analysis or scoring logic in the browser.

D007 adds a direct Report shortcut on results and a shared themed export section
with separate Markdown/HTML actions, busy/error states and document/activity
navigation. Downloaded report content/format remains owned by the backend.
