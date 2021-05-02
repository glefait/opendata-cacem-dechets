FROM python:3.9
WORKDIR /open
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY setup.py README.md ./
COPY src src
RUN pip install . -r requirements.txt
RUN mkdir -p data
ENTRYPOINT ["opendata_cacem_dechets"]
CMD ["get", "--output", "data/cacem-dechets.csv"]