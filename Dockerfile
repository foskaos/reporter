FROM python:3.11

WORKDIR /app

COPY ./reporter_cli/requirements.txt .

RUN pip install -r requirements.txt

COPY . /app

RUN chmod +x /app/Makefile

# Run the make targets for testing, building, and installing
RUN make clean && make test && make build && make install

CMD ["reporter", "--help"]