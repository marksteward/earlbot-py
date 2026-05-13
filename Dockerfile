FROM python

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY earlbot.py .

ENV PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python", "earlbot.py"]
