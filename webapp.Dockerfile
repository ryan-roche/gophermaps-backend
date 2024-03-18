FROM unit:python
LABEL authors="ryan"

COPY requirements.txt /config/requirements.txt
RUN python3 -m pip install -r /config/requirements.txt
EXPOSE 8000
