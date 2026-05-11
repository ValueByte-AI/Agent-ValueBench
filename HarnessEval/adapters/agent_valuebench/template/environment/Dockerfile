FROM python:3.12-alpine

RUN apk add --no-cache curl jq bash nodejs npm git

WORKDIR /app

COPY tool_harness.py /app/tool_harness.py
RUN chmod +x /app/tool_harness.py

RUN mkdir -p /app/env /logs/agent /logs/verifier

CMD ["/bin/bash"]
