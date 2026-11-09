default:
    @just --list

install:
    uv sync --group dev

build:
    sh scripts/build.sh

test:
    uv run pytest -q

demo:
    uv run python scripts/build_demo.py

serve: demo
    uv run python -m http.server 8430 --directory example/_site --bind 127.0.0.1

publish: demo
    uv run smalldocs publish gh-pages example --no-render

# Render fresh working-file consumers, then emit real 390px iframe QA pages.
foundation-fixtures: demo
    uv run python scripts/build_foundation_fixtures.py

# Pinned consuming-site compatibility, isolated from the project's locked baseline.
compat-current:
    uv run --with smalldocs==0.5.5 --with pytest python -m pytest -q
    uv run --with smalldocs==0.5.5 python scripts/build_demo.py
    uv run --with smalldocs==0.5.5 python scripts/build_foundation_fixtures.py
