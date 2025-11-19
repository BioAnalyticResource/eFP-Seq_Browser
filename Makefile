# Validate all
.PHONY: validate-all
validate-all: py-validate
# Validate JavaScript/TypeScript
	@if [ ! -d node_modules ]; then npm ci; fi
	 npm run validate
# Validate R installation
	Rscript -e 'renv::restore()'

# === Python Commands for eFP-Seq_Browser ===
.PHONY: py-install py-format py-lint py-test py-clean py-validate

PY_FILES = cgi-bin/*.cgi

py-install:
	uv pip install -r requirements-dev.txt

py-format:
	uv run ruff format $(PY_FILES)

py-lint:
	uv run ruff check --fix $(PY_FILES)

py-validate: py-install py-format py-lint
