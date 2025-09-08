#!/usr/bin/env node
/**
 * tree.js — create an empty repo skeleton from a fixed list of files.
 * Usage:
 *   node tree.js           # create only missing files
 *   node tree.js --force   # truncate & recreate all listed files (dangerous)
 *   node tree.js --dry-run # print actions only
 */

const fs = require("fs/promises");
const path = require("path");

const DRY = process.argv.includes("--dry-run");
const FORCE = process.argv.includes("--force");

const files = [
  // root
  ".env.example",
  ".gitignore",
  "Dockerfile",
  "docker-compose.yml",
  "Makefile",
  "pyproject.toml",
  "README.md",
  "ARCHITECTURE.md",
  "SECURITY.md",
  "EVALUATION.md",
  "requirements.txt",
  "requirements-dev.txt",

  // app
  "app/__init__.py",
  "app/main.py",
  "app/config.py",
  "app/dependencies.py",

  // app/api
  "app/api/__init__.py",
  "app/api/chat.py",
  "app/api/search.py",
  "app/api/ingest.py",
  "app/api/health.py",
  "app/api/admin.py",

  // app/core
  "app/core/__init__.py",
  "app/core/embeddings.py",
  "app/core/chunker.py",
  "app/core/deduplication.py",
  "app/core/language.py",
  "app/core/retrieval.py",
  "app/core/reranker.py",
  "app/core/generator.py",
  "app/core/citations.py",

  // app/ingest
  "app/ingest/__init__.py",
  "app/ingest/pipeline.py",
  "app/ingest/watcher.py",
  "app/ingest/parsers/__init__.py",
  "app/ingest/parsers/base.py",
  "app/ingest/parsers/pdf.py",
  "app/ingest/parsers/text.py",
  "app/ingest/parsers/docx.py",
  "app/ingest/parsers/csv.py",
  "app/ingest/preprocessor.py",

  // app/storage
  "app/storage/__init__.py",
  "app/storage/vector_store.py",
  "app/storage/document_store.py",
  "app/storage/models.py",
  "app/storage/cache.py",

  // app/ui
  "app/ui/__init__.py",
  "app/ui/routes.py",
  "app/ui/templates/base.html",
  "app/ui/templates/chat.html",
  "app/ui/templates/components/message.html",
  "app/ui/templates/components/source_card.html",
  "app/ui/static/css/main.css",
  "app/ui/static/js/app.js",

  // app/utils
  "app/utils/__init__.py",
  "app/utils/logging.py",
  "app/utils/paths.py",
  "app/utils/tokens.py",

  // cli
  "cli/__init__.py",
  "cli/main.py",
  "cli/commands/__init__.py",
  "cli/commands/ingest.py",
  "cli/commands/search.py",
  "cli/commands/chat.py",
  "cli/commands/admin.py",
  "cli/utils.py",

  // eval
  "eval/__init__.py",
  "eval/datasets/sample_qa.json",
  "eval/datasets/custom_qa.json",
  "eval/metrics.py",
  "eval/runner.py",
  "eval/report.py",

  // tests
  "tests/__init__.py",
  "tests/conftest.py",
  "tests/unit/__init__.py",
  "tests/unit/test_chunker.py",
  "tests/unit/test_embeddings.py",
  "tests/unit/test_retrieval.py",
  "tests/unit/test_parsers.py",
  "tests/unit/test_deduplication.py",
  "tests/integration/__init__.py",
  "tests/integration/test_pipeline.py",
  "tests/integration/test_api.py",
  "tests/e2e/__init__.py",
  "tests/e2e/test_chat_flow.py",

  // scripts
  "scripts/setup.sh",
  "scripts/download_models.py",
  "scripts/migrate_db.py",

  // data & var & snapshots
  "data/.gitkeep",
  "var/index/.gitkeep",
  "var/rag.db",
  "var/logs/.gitkeep",
  "snapshots/.gitkeep",
];

async function ensureDirFor(filePath) {
  const dir = path.dirname(filePath);
  if (dir && dir !== ".") {
    await fs.mkdir(dir, { recursive: true });
  }
}

async function fileExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function createEmpty(p) {
  await ensureDirFor(p);
  await fs.writeFile(p, ""); // empty
}

(async () => {
  let created = 0,
    skipped = 0,
    truncated = 0,
    errors = 0;

  for (const rel of files) {
    const p = path.resolve(process.cwd(), rel);
    const exists = await fileExists(p);

    if (DRY) {
      console.log(
        `${exists ? (FORCE ? "TRUNCATE" : "SKIP") : "CREATE"}  ${rel}`
      );
      continue;
    }

    try {
      if (!exists) {
        await createEmpty(p);
        created++;
        console.log(`CREATE  ${rel}`);
      } else if (FORCE) {
        await fs.truncate(p, 0);
        truncated++;
        console.log(`TRUNCATE  ${rel}`);
      } else {
        skipped++;
        // optional: console.log(`SKIP    ${rel}`);
      }
    } catch (e) {
      errors++;
      console.error(`ERROR   ${rel}: ${e.message}`);
    }
  }

  if (!DRY) {
    console.log(
      `\nDone. created=${created}, truncated=${truncated}, skipped=${skipped}, errors=${errors}`
    );
  } else {
    console.log("\n(DRY RUN) No changes made.");
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
