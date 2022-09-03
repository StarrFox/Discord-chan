FROM python:3.10

RUN python3 -m pip install poetry

WORKDIR /discord_chan

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.in-project true --local
RUN poetry install --only main

COPY . .
CMD [ "poetry", "run", "discord_chan" ]
