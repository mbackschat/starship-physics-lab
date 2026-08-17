---
name: bytebytego-infographic
description: Create original ByteByteGo-inspired technical infographics from verified source material using a panel-based visual system and an image-generation workflow. Use when asked to design, reproduce, revise or quality-check a ByteByteGo-style infographic, especially dense scientific or engineering explainers with exact labels, numbers and provenance.
---

# Create ByteByteGo-inspired infographics

Turn one technical argument into a crisp, original infographic. Borrow the reference set's visual grammar, never its branding, logos, wording or individual illustrations.

## Load the right reference

Always read [references/style.md](references/style.md) before designing or reviewing an infographic.

For the repository's existing Starship poster, also read [references/starship-staging.md](references/starship-staging.md). It is the reproducible content and layout recipe. Do not load it for unrelated subjects.

## Workflow

1. **State one question and one takeaway.** If the material needs two takeaways, make two infographics.
2. **Build a content ledger before prompting.** Record every exact label, number, unit, relationship, source status and required caveat. Mark values as published, estimated, contested or modelled where those distinctions matter.
3. **Verify before publishing.** Run the domain's available checks rather than trusting plausible copy. In this repository, use `review-physics` before placing a physics number in the image. Arithmetic in the poster must close: compositions add to totals, percentages share one denominator and compared values describe the same frame.
4. **Storyboard four to six panels.** Give every panel one job and arrange them as mechanism, comparison, consequence and evidence. Prefer diagrams and aligned comparisons over prose.
5. **Generate an original master.** Use the environment's image-generation capability. Treat any supplied images as style references unless the user explicitly requests an edit. Translate [references/style.md](references/style.md) into the prompt so generation does not depend on external reference files. Require exact text, all units and no extra claims. Exclude ByteByteGo branding and copied illustrations.
6. **Inspect the rendered pixels.** View the full-resolution output and check every label, number, unit, equation, axis, arrow, panel order and conclusion. Text accuracy is a release criterion, not a preference.
7. **Iterate narrowly.** For one local defect, edit only that region and list everything else as an invariant. Recheck the entire poster because image edits can drift outside the requested area.
8. **Save the master, then derive smaller copies deterministically.** Never ask an image model to resize a finished infographic. Preserve the full-resolution PNG and use an ordinary image resizer for thumbnails. In a README, wrap the thumbnail image in a link to the master.

## Prompt contract

Give the image generator:

- use case and intended audience;
- canvas orientation and reading order;
- exact title, subtitle, panel headers, labels and footer;
- one visual mechanism per panel;
- palette, line, typography and spacing rules from the style reference;
- factual constraints and provenance badges;
- explicit exclusions: no logo, watermark, glossy 3D art, decorative space scene, copied artwork or unsupported claim.

Quote exact copy and require it verbatim. Keep labels short enough to survive raster rendering. If the poster needs paragraphs, simplify the content before generation.

## Output contract

Deliver:

- the full-resolution master in the workspace;
- any requested deterministic thumbnail beside it;
- the final prompt or a checked-in recipe that contains the exact copy;
- the verification performed and any remaining uncertainty.

Do not bundle externally supplied reference images into this skill. The written style system is the reusable asset.
