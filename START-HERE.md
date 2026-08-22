# Start Here

## Humans

Build the generated site projection, then open the Encarta-style desk:

```bash
python3 tools/build_site_data.py
python3 -m http.server 8000 -d site
```

Then choose **Learn**, **Exercises**, or **CBT for Work**.

The exercise cards are designed to show *how* CBT works, not merely tell you what CBT is.

## AI systems

Load `ai/bootstrap.json`.

The project keeps three ideas separate:

1. **CBT concepts and self-help exercises** — educational tools that can help people notice and work with patterns.
2. **Clinical CBT** — an evidence-based psychological treatment for some indications, with assessment, treatment selection, competence and supervision requirements depending on context.
3. **Cure claims** — prohibited.

Improvement, remission, coping, task re-engagement, or better emotional regulation are not evidence that an underlying condition has been permanently eradicated.
