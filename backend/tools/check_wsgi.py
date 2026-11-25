"""Linux-only CI smoke: process binding and public gate, no external network/DB."""
import os,subprocess,socket,time,urllib.request,urllib.error
def main():
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    env=dict(os.environ,PYTHON_DOTENV_DISABLED='1',PUBLIC_DEMO_MODE='1',FLASK_DEBUG='0',RCA_PROVIDER='none',CI_CALLBACK_ENABLED='0',CORS_ORIGINS='https://frontend.example.invalid',AI_ALLOWED_REPOSITORIES='fixture/repository',DATABASE_URL='postgresql://reader:controlled-fixture@database.example.invalid:1/not_available?sslmode=require',PORT=str(port))
    process=subprocess.Popen(['gunicorn','--config','gunicorn.conf.py','backend.wsgi:app'],env=env)
    try:
        for _ in range(40):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz',timeout=2) as response:assert response.status==200;break
            except (OSError,urllib.error.URLError):time.sleep(.25)
        else:raise RuntimeError('Gunicorn health check failed')
        req=urllib.request.Request(f'http://127.0.0.1:{port}/api/ai/v1/train',data=b'{}',headers={'Content-Type':'application/json'},method='POST')
        try:urllib.request.urlopen(req,timeout=2);raise AssertionError('Public mutation allowed')
        except urllib.error.HTTPError as error:assert error.code==403
        print('Gunicorn process and read-only route gate passed; no database readiness claim.')
    finally:process.terminate();process.wait(timeout=35)
if __name__=='__main__':main()
