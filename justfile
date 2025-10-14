set windows-shell := ["powershell"]

# show this list
[default]
default:
    just --list

# run tests
test:
    uv run pytest --cov=memobj

# does a version bump commit
bump-commit type="minor": && create-tag
    uv version --bump {{type}}
    git commit -am ("bump to " + (uv version --short))
    git fetch --tags
    git tag (uv version --short)
    git push
    git push --tags

# creates a new tag for the current version
create-tag:
    git fetch --tags
    git tag (uv version --short)
    git push --tags


# update deps
[linux]
update:
    nix flake update
    uv sync --all-groups --upgrade

# update deps
[windows]
update:
    uv sync --all-groups --upgrade


# do a dep bump commit with tag and version
update-commit: update && create-tag
    uv version --bump patch
    git commit -am "bump deps"
    git push

# format
format:
    # TODO: treefmt?
    isort .
    black .
    alejandra .