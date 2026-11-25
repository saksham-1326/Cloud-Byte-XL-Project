import os
bind='0.0.0.0:'+str(int(os.environ.get('PORT','10000')))
workers=1
worker_class='gthread'
threads=4
timeout=120
graceful_timeout=30
accesslog='-'
errorlog='-'
# Omit query strings, authorization headers and request bodies from access logs.
access_log_format='%(h)s %(m)s %(U)s %(s)s %(L)s'
capture_output=True
preload_app=False
