FROM python:3.11-slim

# Environment vars
ENV PYTHONUNBUFFERED True
ENV POETRY_VERSION=1.8.3
ENV APP_HOME /root

# Install Poetry
RUN pip3 install "poetry==$POETRY_VERSION"

# Copy source files
WORKDIR $APP_HOME
COPY pyproject.toml $APP_HOME
COPY /app $APP_HOME/app

# Install project dependencies via poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
