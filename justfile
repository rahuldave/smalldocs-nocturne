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
