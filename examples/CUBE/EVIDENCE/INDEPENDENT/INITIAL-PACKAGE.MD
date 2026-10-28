# Independent Cube package review

Reviewed commit `0346d47af8025e9b854bfcf9af9e3061cb679e86`, baseline `54ede71df5b569c70fb18a3825caf75f88d0406f`.

The delivered ZIPs are intact and reproducible. Two P2 acceptance-tool defects need correction; no additional installer safety or current payload defect was found.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| CUBE.ZIP | 122754 | 9632691c1ed9c168007ffcd27a0c71ecd01d7da940657d3ccf7ba10d74f887b2 |
| CUBESRC.ZIP | 1133646 | f9acd8fbb3330cabaeed3fdbf70c5dba83c59ce5f826849bb14fe9ab66527c5d |

1. **P2, VERIFY.PY:13-18:** Current source and build receipts are verified independently. Updating a semantic CUBE.C source pin while retaining old source-binding/build/native receipts still returns READY. Compare the pinned build/source/runtime maps before accepting qualification.
2. **P2, TESTSRC.PY:14-24:** The complete SOURCE.JSN manifest is ignored. A modified required native build guard passes replay because it is outside ACCEPT.source and unused by RUNHOST. Validate every manifest member and the exact ZIP inventory.

`gate-probes.json` records both reproductions. `tampered-helper-replay/RESULT.JSN` records a successful replay of a deliberately changed build helper while its original manifest hash remained unchanged. These are validator defects; independent inspection confirmed the actual reviewed source archive matches its complete manifest.

Separate gaps: the native gate allows four documented rendering roles to be removed; native recovery fault paths lack injected failure tests. All eight actual rendering fixtures are present. Staging and restore code was inspected with no additional safety issue found.

Independent PACK reproduced both ZIPs byte for byte. The actual source ZIP passed fresh extraction, all 162 declared source hashes and committed bytes, and geometry/config/idle/Hold host checks. The full archive has 334 safe members. Required installer baseline and backup identities match the exact baseline commit; core asset paths are unchanged. No OS media, ROM, installed guest, SDK/DDK, native compiler/emulator binary or unrelated binary toolchain is included. All 24 native render captures and three compact UI captures were inspected.

No emulator was launched and no shared source was edited. Native results here come from independently inspected existing receipts. Effects/Beats owns the shared emulator slot. The complete structured report, reviewed source hashes and evidence hashes are in `REPORT.json`; the exhaustive ZIP/receipt audit is `artifact-audit.json`.
