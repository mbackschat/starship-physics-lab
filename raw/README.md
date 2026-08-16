# Raw sources

Captured source material, immutable. The model reads these and never edits them.

Compiled pages live in [docs/knowledge/](../docs/knowledge/) and cite back to here. The design is in [docs/knowledge-base.md](../docs/knowledge-base.md).

## The rule

**Text only.** A capture is the markdown reduction of a source, plus the URL it came from and the date it was retrieved. No PDFs, no page archives, no video, no images.

Two reasons, and the second is the important one:

1. It keeps the repository small enough to clone quickly.
2. **It keeps a capture diffable.** Recapturing a source later and seeing exactly which numbers moved is the whole reason for keeping the original at all. A binary blob cannot do that.

Anything that will not reduce to text is cited by URL from the page that needs it, and not captured here.

## Naming

```
YYYY-MM-DD-publisher-subject.md
```

The date is when it was *retrieved*, not when the source was published. A source recaptured later gets a new file rather than overwriting the old one, so the two can be diffed.

## Front matter

```yaml
---
resource: https://example.com/article
title: What the source calls itself
retrieved: 2026-08-16
---
```

`retrieved` here becomes `sources[].last_modified` on the pages that cite it, which is the OKF field for source recency.
