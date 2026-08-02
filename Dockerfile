# syntax=docker/dockerfile:1

FROM python:3.11.8-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/ .

# Debug: dump exact content at line 1192
RUN python3 -c "
with open('server.py','rb') as f:
    raw = f.read()
lines = raw.split(b'\n')
print('Total bytes:', len(raw))
print('CR count:', raw.count(b'\r'))
print('LF count:', raw.count(b'\n'))
print('Total lines:', len(lines))
if len(lines) > 1190:
    print('Line 1190:', repr(lines[1189]))
    print('Line 1191:', repr(lines[1190]))
    print('Line 1192:', repr(lines[1191]))
    print('Line 1193:', repr(lines[1192]))
    print('Line 1194:', repr(lines[1193]))
    # Find all 'except' with no matching 'try'
    for i, line in enumerate(lines):
        s = line.strip()
        if s == 'except Exception:':
            # Check if previous non-empty line has content under a try
            prev_code = ''
            for j in range(i-1, max(i-5, -1), -1):
                ps = lines[j].strip()
                if ps:
                    prev_code = ps
                    break
            if prev_code == 'try:' or prev_code == '':
                print(f'  SUSPECT at line {i+1}: prev={repr(prev_code)}, curr={repr(s)}')
"

# Validate syntax at build time
RUN python3 -c "import py_compile; py_compile.compile('server.py', doraise=True); print('SYNTAX OK: server.py')"

# Create data directory
RUN mkdir -p /data && chmod +x entrypoint.sh

# Set environment
ENV DATA_DIR=/data
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["./entrypoint.sh"]
