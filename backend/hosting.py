"""Fail-closed Render public-demo profile; local behavior remains separate."""
import os,logging,ipaddress
from urllib.parse import urlsplit
from flask import request,jsonify
from .database import configuration
from .ai_intelligence.github import repository_name,redact

PUBLIC_READS={'/','/healthz','/readyz','/api/github/repository/latest',
             *('/api/ai/v1/'+p for p in ['overview','runs','predictions','models','rca','evaluation','outcomes'])}
PUBLIC_POST_READS={'/api/github/repository','/api/github/file'}

def validate_environment(env=None):
    e=os.environ if env is None else env
    if e.get('PUBLIC_DEMO_MODE')!='1':raise ValueError('Hosted entry point requires PUBLIC_DEMO_MODE=1.')
    if e.get('RCA_PROVIDER','none')!='none' or e.get('CI_CALLBACK_ENABLED','0')!='0' or e.get('FLASK_DEBUG','0')!='0':
        raise ValueError('Hosted public demo requires providers, callbacks and debug disabled.')
    origins=[x.strip() for x in e.get('CORS_ORIGINS','').split(',') if x.strip()]
    for origin in origins:
        u=urlsplit(origin)
        if u.scheme!='https' or not u.hostname or u.hostname in ('localhost','127.0.0.1','::1') or u.username or u.password or u.path or u.query or u.fragment or '*' in origin:
            raise ValueError('CORS_ORIGINS must contain exact HTTPS frontend origins.')
    if not origins:raise ValueError('Explicit CORS_ORIGINS required.')
    repos={repository_name(x.strip()) for x in e.get('AI_ALLOWED_REPOSITORIES','').split(',') if x.strip()}
    if not repos:raise ValueError('Explicit AI_ALLOWED_REPOSITORIES required.')
    cfg=configuration(e)
    if not all(cfg.get(k) for k in ('host','dbname','user','password')) or cfg.get('sslmode') not in ('require','verify-ca','verify-full'):
        raise ValueError('Explicit PostgreSQL identity and TLS mode required.')
    host=cfg.get('host','')
    try:is_local=ipaddress.ip_address(host).is_loopback
    except ValueError:is_local=host.lower()=='localhost'
    if is_local:raise ValueError('Hosted database must not use loopback.')
    return repos

class SafeLogFilter(logging.Filter):
    def filter(self,record):
        record.msg=redact(record.getMessage());record.args=()
        if record.exc_info:
            # Keep traceback types internally safe; connection exceptions can
            # contain DSNs. No credential-bearing exception text is emitted.
            record.msg+=' ['+record.exc_info[0].__name__+']';record.exc_info=None;record.exc_text=None
        return True

def register_public_demo(app,connect,allowed):
    app.config.update(DEBUG=False,MAX_CONTENT_LENGTH=65536,PROPAGATE_EXCEPTIONS=False)
    for handler in app.logger.handlers:handler.addFilter(SafeLogFilter())
    @app.before_request
    def public_gate():
        path=request.path
        if request.method=='OPTIONS':
            if path in PUBLIC_READS|PUBLIC_POST_READS:return None
            return jsonify(status='FAILED',message='Endpoint unavailable in public demo.'),403
        if request.method in ('GET','HEAD') and path in PUBLIC_READS:return None
        if request.method=='POST' and path in PUBLIC_POST_READS:
            data=request.get_json(silent=True)
            if not isinstance(data,dict):return jsonify(status='FAILED',message='JSON object required.'),400
            raw=data.get('url','')
            if not isinstance(raw,str):return jsonify(status='FAILED',message='Repository URL required.'),400
            u=urlsplit(raw);parts=u.path.strip('/').removesuffix('.git').split('/')
            if u.scheme!='https' or u.hostname!='github.com' or u.username or u.password or u.query or u.fragment or len(parts)!=2:
                return jsonify(status='FAILED',message='Approved HTTPS GitHub repository URL required.'),400
            if '/'.join(parts).lower() not in allowed:return jsonify(status='FAILED',message='Repository is not allowlisted.'),403
            return None
        return jsonify(status='FAILED',message='Endpoint unavailable in read-only public demo.'),403
    @app.get('/healthz')
    def health():return jsonify(status='SUCCESS',mode='public_read_only'),200
    @app.get('/readyz')
    def ready():
        try:
            with connect() as conn:
                if conn.execute('SHOW transaction_read_only').fetchone()[0]!='on':raise ValueError()
                if conn.execute("SELECT count(*) FROM ai_schema_migrations").fetchone()[0]!=5:raise ValueError()
                if conn.execute("SELECT to_regclass('public.repositories')").fetchone()[0] is None:raise ValueError()
                privileges=conn.execute("""SELECT rolsuper,rolcreatedb,rolcreaterole,
                    has_table_privilege(current_user,'public.repositories','INSERT')
                    FROM pg_roles WHERE rolname=current_user""").fetchone()
                if privileges!=(False,False,False,False):raise ValueError()
            return jsonify(status='SUCCESS'),200
        except Exception:return jsonify(status='FAILED',message='Database readiness check failed.'),503
    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Cache-Control']='no-store'
        if response.status_code>=500:
            response.set_data(app.json.dumps({'status':'FAILED','message':'Service temporarily unavailable.'}));response.content_type='application/json'
        return response
