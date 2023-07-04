default: commit push

commit:
    git add .
    cz commit

push:
    git push

bump:
    cz bump
    git push
    git push --tags

update:
    nix flake update
    poetry update

run:
    poetry run discord-chan --debug

# TODO: treefmt?
format:
    isort .
    black .
    alejandra .
