"""One-shot native Windows verification. No cloud keys, no owner files."""
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
import traceback
import urllib.request

from winpty import PtyProcess

ROOT = Path(r'C:\FCCGuideHarness')
PS = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
RESULT = {'status': 'running', 'started': time.time(), 'stages': []}
CHILDREN = []
PROMPT = 'Напиши одно короткое вежливое сообщение клиенту по-русски: сегодня не успеваю закончить задачу, пришлю её завтра к обеду. Начни словом «Извините». Дай только текст сообщения'


def progress(message):
    with (ROOT / 'progress.txt').open('a', encoding='utf-8') as f:
        f.write(time.strftime('%H:%M:%S ') + message + '\n')
    print(message, flush=True)


def psargs(code):
    encoded = base64.b64encode(code.encode('utf-16le')).decode()
    return [PS, '-NoLogo', '-NoProfile', '-EncodedCommand', encoded]


def run_ps(code, name, timeout=900):
    progress(name)
    completed = subprocess.run(psargs("[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); $ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; " + code), capture_output=True, timeout=timeout)
    text = completed.stdout.decode('utf-8', errors='replace') + completed.stderr.decode('utf-8', errors='replace')
    (ROOT / (name + '.txt')).write_text(text, encoding='utf-8')
    if completed.returncode:
        raise RuntimeError(name + ': ' + text[-4000:])
    return text


class Terminal:
    def __init__(self, args, name, cwd=None):
        self.p = PtyProcess.spawn(args, cwd=cwd, dimensions=(50, 180), env=dict(os.environ))
        self.name = name
        self.q = queue.Queue()
        self.text = ''
        self.closed = False
        self.thread = threading.Thread(target=self.read, daemon=True)
        self.thread.start()
        CHILDREN.append(self)

    def read(self):
        with (ROOT / (self.name + '.txt')).open('w', encoding='utf-8') as f:
            while not self.closed:
                try:
                    chunk = self.p.read(65536)
                except (EOFError, OSError):
                    break
                f.write(chunk)
                f.flush()
                self.q.put(chunk)

    def pump(self):
        while True:
            try:
                self.text += self.q.get_nowait()
            except queue.Empty:
                break
        return re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', self.text)

    def wait_for(self, value, timeout=120):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            text = self.pump()
            if value in text:
                return text
            if not self.p.isalive():
                self.pump()
                raise RuntimeError(self.name + ' exited before ' + value + ': ' + self.text[-3000:])
            time.sleep(.2)
        raise TimeoutError(self.name + ': ' + value + ': ' + self.text[-3000:])

    def stop(self):
        if self.p.isalive():
            self.p.write('\x03')
            time.sleep(.5)
            if self.p.isalive():
                self.p.write('\x03')
            end = time.monotonic() + 4
            while self.p.isalive() and time.monotonic() < end:
                time.sleep(.2)
            if self.p.isalive():
                subprocess.run(['taskkill', '/PID', str(self.p.pid), '/T', '/F'], capture_output=True, timeout=15)
        self.closed = True


def wait_url(url, timeout=120):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return json.load(r)
        except Exception:
            time.sleep(1)
    raise TimeoutError(url)


def save_receipts():
    rows = []
    logs = Path.home() / '.fcc/logs/server.log'
    if logs.exists():
        for line in logs.read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                row = json.loads(line)
                row = row.get('record', {}).get('extra', row)
            except ValueError:
                continue
            # Only non-secret request receipt fields are exported.
            if row.get('event') == 'request.completed' or row.get('outcome'):
                rows.append({k: row.get(k) for k in ['event', 'request_id', 'provider_id', 'model', 'status_code', 'outcome', 'duration_ms']})
    (ROOT / 'request-receipts.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    return rows


def main():
    progress('Starting native Windows test')
    identity = subprocess.check_output(['whoami'], text=True).strip()
    profile = Path.home()
    RESULT['identity'] = identity
    RESULT['profile_name'] = profile.name
    assert identity.lower().endswith('\\fccguidetest'), identity
    assert profile.name.lower() == 'fccguidetest', str(profile)
    # Keep native OS profile variables; remove inherited CI/provider credentials and developer tool paths.
    keep = {'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'HOMEDRIVE', 'HOMEPATH', 'USERNAME', 'USERDOMAIN', 'COMPUTERNAME', 'PROCESSOR_ARCHITECTURE', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PROGRAMDATA', 'PUBLIC', 'ALLUSERSPROFILE'}
    for key in list(os.environ):
        if key.upper() not in keep:
            os.environ.pop(key)
    os.environ['PATH'] = os.pathsep.join([str(Path(os.environ['SystemRoot']) / 'System32'), os.environ['SystemRoot'], str(Path(PS).parent)])
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    for directory in ['Downloads', 'Desktop']:
        (profile / directory).mkdir(exist_ok=True)
    RESULT['baseline'] = run_ps("Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | ConvertTo-Json; $PSVersionTable.PSVersion.ToString(); foreach($c in 'claude','uv','fcc-server','ollama','git'){ $x=Get-Command $c -ErrorAction SilentlyContinue; if($x){Write-Output ($c+': '+$x.Source)}else{Write-Output ($c+': absent')} }", 'baseline')
    assert not (profile / '.fcc').exists()
    assert not (profile / '.claude').exists()
    install = r'''$env:FCC_INSTALL_VERSION='6.18.5'; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Alishahryar1/free-claude-code/v6.18.5/scripts/install.ps1' -OutFile "$env:USERPROFILE\Downloads\free-claude-code-install.ps1"; & ([scriptblock]::Create((Get-Content -Raw "$env:USERPROFILE\Downloads\free-claude-code-install.ps1"))); if(-not $?) {exit 1}'''
    terminal = Terminal(psargs(install), 'installer')
    for label in ['Claude Code', 'Codex', 'Pi', 'OpenCode', 'Cline CLI', 'Hermes Agent', 'DeepSeek Harness', 'Grok Build', 'Muse Code', 'Aider', 'Antigravity CLI']:
        terminal.wait_for('Install ' + label + ' for', timeout=180)
        terminal.p.write(('y' if label == 'Claude Code' else 'n') + '\r\n')
    terminal.wait_for('Enable RTK + Headroom', timeout=180)
    terminal.p.write('n\r\n')
    end = time.monotonic() + 900
    while terminal.p.isalive() and time.monotonic() < end:
        terminal.pump()
        time.sleep(1)
    terminal.pump()
    if terminal.p.isalive() or terminal.p.exitstatus != 0:
        raise RuntimeError('Native installer failed: ' + terminal.text[-5000:])
    RESULT['stages'].append('native FCC installer completed')
    refresh = r'''$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User');'''
    RESULT['versions'] = run_ps(refresh + 'fcc-server --version; claude --version; uv --version; if($LASTEXITCODE -ne 0){exit 1}', 'versions')
    # Exact Windows archive and hash from the article.
    setup = r'''$fccOllamaDir=Join-Path $env:LOCALAPPDATA 'fcc-local\ollama-0.40.13'; New-Item -ItemType Directory -Path $fccOllamaDir -Force|Out-Null; Invoke-WebRequest -Uri 'https://github.com/ollama/ollama/releases/download/v0.40.13/ollama-windows-amd64.zip' -OutFile "$fccOllamaDir\package.zip"; if((Get-FileHash "$fccOllamaDir\package.zip" -Algorithm SHA256).Hash -ne '7afa38624fa62ee5d8293422d0ab084c1bb4603134c7f4dafce11a033b57cc19'){throw 'Archive hash mismatch'}; Expand-Archive -LiteralPath "$fccOllamaDir\package.zip" -DestinationPath $fccOllamaDir -Force'''
    run_ps(setup, 'ollama-install')
    serve = r'''$env:OLLAMA_HOST='127.0.0.1:11435'; $env:OLLAMA_MODELS=Join-Path $env:LOCALAPPDATA 'fcc-local\models'; $env:OLLAMA_CONTEXT_LENGTH='32768'; $env:OLLAMA_NO_CLOUD='1'; & "$env:LOCALAPPDATA\fcc-local\ollama-0.40.13\ollama.exe" serve'''
    Terminal(psargs(serve), 'ollama-server')
    wait_url('http://127.0.0.1:11435/api/tags')
    run_ps(r'''$env:OLLAMA_HOST='127.0.0.1:11435'; & "$env:LOCALAPPDATA\fcc-local\ollama-0.40.13\ollama.exe" pull qwen3:4b-instruct; if($LASTEXITCODE -ne 0){exit 1}''', 'model-pull')
    RESULT['models'] = wait_url('http://127.0.0.1:11435/api/tags')
    server = refresh + r'''$env:MODEL='ollama/qwen3:4b-instruct'; $env:REASONING_POLICY='off'; $env:OLLAMA_BASE_URL='http://127.0.0.1:11435'; $env:HTTP_READ_TIMEOUT='900'; $env:PROVIDER_PROGRESS_TIMEOUT='1200'; $env:HOST='127.0.0.1'; $env:FCC_OPEN_BROWSER='false'; fcc-server'''
    fcc = Terminal(psargs(server), 'fcc-server')
    fcc.wait_for('Application startup complete', timeout=120)
    testdir = profile / ('fcc-first-run-' + str(int(time.time())))
    testdir.mkdir()
    q = PROMPT.replace("'", "''")
    client = refresh + "$env:CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT='1'; "
    command = client + f"Set-Location -LiteralPath '{testdir}'; fcc-claude --tools Read -p '{q}' --output-format json; if($LASTEXITCODE -ne 0){{exit 1}}"
    RESULT['first_answer'] = run_ps(command, 'first-answer', timeout=900)
    fcc.stop()
    time.sleep(3)
    fcc = Terminal(psargs(server), 'fcc-restarted')
    fcc.wait_for('Application startup complete', timeout=120)
    RESULT['restart_answer'] = run_ps(command, 'restart-answer', timeout=900)
    for key in ['first_answer', 'restart_answer']:
        answer = json.loads(RESULT[key].strip())
        assert not answer.get('is_error'), answer
        assert 'Извините' in answer.get('result', '') and 'завтра' in answer.get('result', ''), answer
    progress('reader-plain-text-output')
    reader_command = command.replace(' --output-format json', '')
    console = Terminal(psargs(reader_command), 'reader-plain-text')
    end = time.monotonic() + 300
    while console.p.isalive() and time.monotonic() < end:
        console.pump()
        time.sleep(.2)
    text = console.pump()
    assert not console.p.isalive(), 'Reader one-shot command did not return'
    assert 'Извините' in text and 'завтра' in text, text[-3000:]
    RESULT['reader_plain_text'] = text
    RESULT['interactive'] = {'tested': False, 'reason': 'Article first-response path uses the official one-shot -p mode'}
    RESULT['receipts'] = save_receipts()
    RESULT['status'] = 'response_received_review_required'


try:
    main()
except Exception:
    RESULT['status'] = 'failed'
    RESULT['error'] = traceback.format_exc()
    progress(RESULT['error'])
finally:
    save_receipts()
    for child in reversed(CHILDREN):
        try:
            child.stop()
        except Exception:
            pass
    RESULT['finished'] = time.time()
    (ROOT / 'result.json').write_text(json.dumps(RESULT, ensure_ascii=False, indent=2), encoding='utf-8')
# All evidence is flushed. Avoid waiting for a ConPTY reader during interpreter teardown.
os._exit(1 if RESULT['status'] == 'failed' else 0)
