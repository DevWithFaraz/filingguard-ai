---
type: guide
status: inventoried-local
date: 2026-10-11
tags: [delivery, attribution]
---
# Third-party notices

Related: [[docs/delivery/README]], [[README]], [[TODO]] T059,
[[apps/web/src/assets/README]], [[data/demo/curated-v1/README]], [[apps/video/README]].

## Locked dependency evidence

The October 11 fresh locked install contains 32 packages in the browser dependency
closure. Their metadata, upstream links, copyright and supplied license files are
preserved in [browser notices](../../apps/web/public/third-party-notices.txt), served
at `/third-party-notices.txt` and copied unchanged into the production build.
This closure includes dependencies that may be tree-shaken out; it is conservative,
not an exact bundle manifest. MIT/BSD notices are retained rather than replaced
by a list of package names. GSAP and @gsap/react supply a license URL instead of a
separate license file; that URL is retained in the notice artifact.

The 52 installed Python dependencies, including development/probe tools, have
supplied license files. Metadata, upstream links and complete supplied texts are
preserved in [API notices](api-dependency-notices.txt). The runtime's declaration
is `apps/api/pyproject.toml`; `apps/api/uv.lock` pins resolved versions. This inventory
is not limited to server production dependencies and does not claim every nested
native-library notice has been independently audited.

Regenerate from a locked installation at the repository root:

```powershell
node scripts/export_browser_notices.mjs
node scripts/api.mjs run python ../../scripts/export_api_notices.py
```

Review changes and missing-file warnings after dependency upgrades. Full inventory
JSON is diagnostic output in ignored `.runtime/t059`; distributed texts are retained
in the paths above. No provider calls, credentials or filing text are involved.

## Terms needing distinct treatment

GSAP uses its own [standard license](https://gsap.com/community/standard-license/),
not MIT. The current license permits website use and restricts competing visual
animation builders. FilingGuard uses GSAP for interface motion; this scope is an
inference from the implemented product, not permission for a future animation tool.
Keep vendor copyright/license headers intact.

Python metadata includes LGPL-3.0-only for psycopg/psycopg-binary, MPL-2.0 for
certifi, MPL-2.0/MIT for tqdm and Apache/CNRI terms for regex. Consult their retained
texts and upstream links when redistributing server binaries or modified libraries;
do not label the dependency set entirely MIT. This pass inventories evidence and
does not provide legal clearance for every future packaging/distribution model.

Remotion is a separate authoring tool, not browser runtime. Its installed
`node_modules/remotion/LICENSE.md` grants its free tier to individuals and eligible
small organizations. The recorded solo participant fits the individual category;
recheck terms if the operator changes. Preserve its license and third-party notices
when redistributing authoring software. Website film assets are locally rendered;
[[apps/video/README]] owns their source/render provenance.

## Supplied assets and opinion sources

[[apps/web/src/assets/README]] owns exact filenames, hashes and provenance for the
user's logo/background and GC Avalance font faces. The font download says personal
use; the user reported direct creator permission for this site and authorized use.
That private permission has not been independently inspected. Retain its record
privately; do not invent a public license or repeat the authorization request.
The supplied background has no independent license document in the repository.

[[data/demo/curated-v1/README]] and its `sources.json` own public opinion URLs,
retrieval dates and hashes. Synthetic filings and expected verdicts are identified
separately. Source attribution does not establish that a verdict is legally correct.

The application has no declared source redistribution license. Private npm package
metadata and third-party permissions do not grant a license to FilingGuard's own
source. Choosing an application license remains an owner decision.
