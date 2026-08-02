FROM python:3.11.8-slim

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ .

RUN python3 -c "
import glob, os
for pattern in ['**/*.py','**/*.sh','**/*.txt','**/*.yaml','**/*.yml','**/*.json','**/*.html','**/*.css','**/*.js']:
    for f in glob.glob(pattern, recursive=True):
        data = open(f,'rb').read()
        if b'\r\n' in data:
            open(f,'wb').write(data.replace(b'\r\n',b'\n'))
            print(f'Fixed CRLF: {f}')
print('CRLF normalization done')
" && \
    chmod +x entrypoint.sh && \
    mkdir -p /data

ENV DATA_DIR=/data
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["./entrypoint.sh"]
