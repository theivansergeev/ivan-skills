"""Fresh hosted macOS: native official installer and actual local inference."""
import fcntl,hashlib,json,os,pty,re,select,subprocess,termios,time,traceback,urllib.request
from pathlib import Path

OUT=Path('/private/tmp/FCCMacEvidence');OUT.mkdir(exist_ok=True)
profile=Path.home()
env={k:os.environ[k] for k in ['HOME','USER','LOGNAME','TMPDIR','LANG'] if k in os.environ}
env['PATH']='/usr/bin:/bin:/usr/sbin:/sbin';env['TERM']='xterm-256color'
children=[];result={'status':'running','started':time.time()}
prompt='Напиши одно короткое вежливое сообщение клиенту по-русски: сегодня не успеваю закончить задачу, пришлю её завтра к обеду. Начни словом «Извините». Дай только текст сообщения'

def run(args,name,timeout=900):
    r=subprocess.run(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    text=r.stdout.decode('utf-8',errors='replace');(OUT/(name+'.txt')).write_text(text)
    if r.returncode:raise RuntimeError(name+': '+text[-3000:])
    return text

class Console:
    def __init__(self,args,name):
        def controlling_tty():
            os.setsid()
            fcntl.ioctl(0,termios.TIOCSCTTY,0)
        self.master,slave=pty.openpty();self.p=subprocess.Popen(args,env=env,stdin=slave,stdout=slave,stderr=slave,preexec_fn=controlling_tty);os.close(slave)
        self.text='';self.log=(OUT/(name+'.txt')).open('w');children.append(self)
    def pump(self):
        if select.select([self.master],[],[],.2)[0]:
            try:data=os.read(self.master,65536).decode(errors='replace')
            except OSError:data=''
            self.text+=data;self.log.write(data);self.log.flush()
        return re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',self.text)
    def wait(self,needle,timeout=180):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            if needle in self.pump():return
            if self.p.poll() is not None:raise RuntimeError(self.text[-3000:])
        raise TimeoutError(needle+': '+self.text[-3000:])
    def stop(self):
        if self.p.poll() is None:
            import signal
            os.killpg(self.p.pid,signal.SIGINT)
            try:self.p.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(self.p.pid,signal.SIGTERM)

def background(args,name):
    f=(OUT/(name+'.txt')).open('w');p=subprocess.Popen(args,env=env,stdout=f,stderr=subprocess.STDOUT);children.append(p);return p

def ready(url):
    for _ in range(120):
        try:
            with urllib.request.urlopen(url,timeout=2) as r:
                if r.status==200:return
        except Exception:time.sleep(1)
    raise TimeoutError(url)

try:
    result['baseline']=run(['/bin/sh','-c','sw_vers;uname -m;for c in claude uv fcc-server ollama;do command -v "$c" || true;done'],'baseline')
    assert not (profile/'.fcc').exists()
    assert not (profile/'.claude').exists()
    (profile/'Downloads').mkdir(exist_ok=True)
    # Avoid the confirmed +gil selector failure in FCC's macOS shell installer.
    # Use the same official native client, package and exact CPython version directly.
    uv_installer=profile/'Downloads/fcc-uv-install.sh'
    run(['/usr/bin/curl','-fL','https://astral.sh/uv/0.13.6/install.sh','-o',str(uv_installer)],'download-uv-installer')
    run(['/bin/sh',str(uv_installer)],'install-uv')
    client_installer=profile/'Downloads/fcc-claude-install.sh'
    run(['/usr/bin/curl','-fL','https://claude.ai/install.sh','-o',str(client_installer)],'download-client-installer')
    run(['/bin/bash',str(client_installer),'2.1.314'],'install-client')
    run([str(profile/'.local/bin/uv'),'tool','install','--managed-python','--python','3.14.10','free-claude-code==6.18.5'],'install-fcc')
    run([str(profile/'.local/bin/uv'),'tool','update-shell'],'update-shell')
    env['PATH']=str(profile/'.local/bin')+':'+env['PATH']
    result['versions']=run(['/bin/sh','-c','fcc-server --version;claude --version;uv --version'],'versions')
    ollama=profile/'fcc-local/ollama-0.40.13';ollama.mkdir(parents=True)
    archive=ollama/'package.tgz'
    run(['/usr/bin/curl','-fL','https://github.com/ollama/ollama/releases/download/v0.40.13/ollama-darwin.tgz','-o',str(archive)],'download-ollama')
    assert hashlib.sha256(archive.read_bytes()).hexdigest()=='bae29252232b9e1358cf5801a7d65a07442af18fb5467cb68c7fc3711f59c511'
    run(['/usr/bin/tar','-xzf',str(archive),'-C',str(ollama)],'extract-ollama')
    env.update({'OLLAMA_HOST':'127.0.0.1:11435','OLLAMA_MODELS':str(profile/'fcc-local/models'),'OLLAMA_CONTEXT_LENGTH':'32768','OLLAMA_NO_CLOUD':'1'})
    background([str(ollama/'ollama'),'serve'],'ollama-server');ready('http://127.0.0.1:11435/api/tags')
    run([str(ollama/'ollama'),'pull','qwen3:4b-instruct'],'model-pull')
    env.update({'MODEL':'ollama/qwen3:4b-instruct','REASONING_POLICY':'off','OLLAMA_BASE_URL':'http://127.0.0.1:11435','HOST':'127.0.0.1','FCC_OPEN_BROWSER':'false','HTTP_READ_TIMEOUT':'900','PROVIDER_PROGRESS_TIMEOUT':'1200','CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT':'1'})
    fcc=background([str(profile/'.local/bin/fcc-server')],'fcc-server');ready('http://127.0.0.1:8082/health')
    project=profile/'fcc-first-run-native';project.mkdir();os.chdir(project)
    args=[str(profile/'.local/bin/fcc-claude'),'--tools','Read','-p',prompt,'--output-format','json']
    for name in ['first-answer','restart-answer']:
        if name=='restart-answer':
            fcc.terminate();fcc.wait(timeout=15)
            fcc=background([str(profile/'.local/bin/fcc-server')],'fcc-restarted');ready('http://127.0.0.1:8082/health')
        text=run(args,name,timeout=900);answer=json.loads(text.strip());assert not answer.get('is_error'),answer
        assert 'Извините' in answer.get('result','') and 'завтра' in answer.get('result',''),answer
        result[name]=answer
    result['status']='response_received_review_required'
except Exception:result.update(status='failed',error=traceback.format_exc())
finally:
    receipts=[]
    log=profile/'.fcc/logs/server.log'
    if log.exists():
        for line in log.read_text(errors='replace').splitlines():
            try:r=json.loads(line).get('record',{}).get('extra',{})
            except ValueError:continue
            if r.get('event')=='request.completed':receipts.append({k:r.get(k) for k in ['request_id','provider_id','model','status_code','outcome','duration_ms']})
    result['receipts']=receipts
    for p in reversed(children):
        try:
            if isinstance(p,Console):p.stop()
            elif p.poll() is None:p.terminate();p.wait(timeout=10)
        except Exception:pass
    result['finished']=time.time();(OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
if result['status']=='failed':raise SystemExit(1)
