# Code-model training boundary

The Code specialist is a separate model path. It does not consume Writer prose, Writer datasets, Writer adapters, Writer embeddings, or Writer evaluations.

Before any Code import, inspect the intended repository only:

```bash
.venv/bin/sixai code inspect "/ABSOLUTE/PATH/TO/YOUR/CODE-REPOSITORY"
```

The inspector accepts source and selected configuration formats, excludes generated/dependency directories, scans for likely secrets, and copies nothing. After its report is reviewed, import explicitly:

```bash
.venv/bin/sixai code import "/ABSOLUTE/PATH/TO/YOUR/CODE-REPOSITORY"
```

`writings` is excluded by default. Add `--exclude-dir NAME` again for each additional top-level library that should never enter Code training.

For a large multi-project workspace, inventory it in read-only batches before importing anything:

```bash
.venv/bin/sixai code workspace-inspect "/ABSOLUTE/PATH/TO/WORKSPACE" --limit 10
.venv/bin/sixai code workspace-inspect "/ABSOLUTE/PATH/TO/WORKSPACE" --offset 10 --limit 10
```

Each batch writes a local report under `reports/code/`. We use the inventory to balance projects in the future Code dataset; a multi-gigabyte app must not outweigh a smaller app merely because it has more generated or duplicate code.

This writes only to `corpora/code/`. A future Code base-model download is separate:

```bash
.venv/bin/sixai model status code
.venv/bin/sixai model download code
```

You can already use the unmodified local Code base without storing any code:

```bash
.venv/bin/sixai code chat "Write a Swift function that reverses a string." -n 120
```

The initial `raastey-work` workspace import is now complete, excluding `writings` and the `model-training` laboratory. It contains 9,788 unique, locally stored Code files after content-hash deduplication. Ten likely-secret files were quarantined and were never copied. No Code dataset or adapter has been created yet.
