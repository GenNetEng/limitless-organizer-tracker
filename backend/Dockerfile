FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e ".[dev]" && chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
