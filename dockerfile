FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y curl unzip && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deno.land/install.sh | sh

RUN mkdir -p /etc/yt-dlp && \
    printf '%s\n' '--remote-components' 'ejs:github' > /etc/yt-dlp.conf

ENV PATH="/root/.deno/bin:${PATH}"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]