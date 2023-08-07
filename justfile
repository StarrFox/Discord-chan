# show this list
default:
    just --list

# commit then push
commit-push: commit push

# bump version
bump type: && create-tag
    poetry version {{type}}

# creates a new tag for the current version
create-tag:
    git fetch --tags
    poetry version | awk '{print $2}' | xargs git tag

# update deps
update:
    nix flake update
    # the poetry devs dont allow this with normal update for some unknown reason
    poetry up --latest

# run debug build
run:
    nix run . -- --debug

# format
format:
    # TODO: treefmt?
    isort .
    black .
    alejandra .
