# Reproducing the Starship infographic

For the exact approved pixels, use the [full-resolution master](images/starship-staging-infographic.png). Image generation is stochastic, so regenerating produces an equivalent poster rather than a pixel-identical copy.

To regenerate it, open Codex in this repository and send:

```text
$bytebytego-infographic Reproduce the existing Starship staging infographic from the checked-in recipe. Reverify the physics, generate a new full-resolution master, inspect every label and number, and fix any rendering errors. Do not use the Desktop reference images. Save it non-destructively as docs/images/starship-staging-infographic-v2.png.
```

The skill loads its general visual system and the specific [Starship recipe](../.claude/skills/bytebytego-infographic/references/starship-staging.md). The versioned filename preserves the approved original for comparison. See [OpenAI's reusable Codex skills guide](https://learn.chatgpt.com/use-cases/reusable-codex-skills) for the general workflow.
