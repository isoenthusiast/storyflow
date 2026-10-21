#!/usr/bin/env python3
"""Local editorial desk. No WordPress credentials or automatic publication."""
import argparse
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
STAGES = ['idea', 'research', 'drafting', 'review', 'ready', 'scheduled', 'published']
FIELDS = ['title', 'stage', 'angle', 'audience', 'experience', 'sources', 'draft', 'notes',
          'format', 'target_date', 'wordpress_url', 'narration', 'checks', 'archived',
          'conversation', 'decisions', 'questions', 'next_action', 'chat_reference']
CHECKS = ['voice', 'facts', 'structure', 'disclosure']


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS ideas (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS revisions (id INTEGER PRIMARY KEY, idea_id TEXT, data TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS activity (id INTEGER PRIMARY KEY, idea_id TEXT, data TEXT NOT NULL)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def all(self):
        with self.connect() as db:
            return sorted([self.defaults(json.loads(r[0])) for r in db.execute('SELECT data FROM ideas')],
                          key=lambda x: x['updated_at'], reverse=True)

    @staticmethod
    def defaults(item):
        for field in FIELDS:
            item.setdefault(field, '')
        return item

    def save(self, payload, ident=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = None
            if ident:
                row = db.execute('SELECT data FROM ideas WHERE id=?', (ident,)).fetchone()
                if not row:
                    raise LookupError('Idea not found.')
                old = self.defaults(json.loads(row[0]))
                if payload.get('version') != old['version']:
                    raise RuntimeError('This idea changed in another tab. Copy your changes before reopening it.')
            item = {k: payload.get(k, old.get(k, '') if old else '') for k in FIELDS}
            source = payload.get('update_source', 'desk')
            activity_note = payload.get('activity_note', '')
            if source not in ['desk', 'chat'] or not isinstance(activity_note, str) or len(activity_note) > 4000:
                raise ValueError('Invalid activity details.')
            for k in FIELDS:
                if k not in ['checks', 'archived'] and not isinstance(item[k], str):
                    raise ValueError('Text fields must contain text.')
            item['title'] = item['title'].strip()
            if not item['title'] or len(item['title']) > 250:
                raise ValueError('Add a title of 1–250 characters.')
            item['stage'] = item['stage'] or 'idea'
            if item['stage'] not in STAGES:
                raise ValueError('Unknown stage.')
            item['format'] = item['format'] or 'Practical article'
            item['narration'] = item['narration'] or 'Not started'
            if item['target_date']:
                date.fromisoformat(item['target_date'])
            if item['wordpress_url']:
                url = urlsplit(item['wordpress_url'])
                if url.scheme not in ['http', 'https'] or not url.netloc:
                    raise ValueError('Use a complete http or https publication link.')
            if item['stage'] in ['scheduled', 'published'] and not item['wordpress_url']:
                raise ValueError('Add the publication link before recording this stage.')
            if item['stage'] == 'scheduled' and not item['target_date']:
                raise ValueError('Add the confirmed scheduled date.')
            item['checks'] = item['checks'] or []
            if not isinstance(item['checks'], list) or any(x not in CHECKS for x in item['checks']):
                raise ValueError('Invalid review checklist.')
            if item['archived'] == '':
                item['archived'] = False
            if not isinstance(item['archived'], bool):
                raise ValueError('Invalid archive value.')
            item.update(id=ident or uuid4().hex, created_at=old['created_at'] if old else now(),
                        updated_at=now(), version=old['version'] + 1 if old else 1)
            if old:
                db.execute('INSERT INTO revisions (idea_id,data) VALUES (?,?)', (ident, json.dumps(old)))
            db.execute('INSERT OR REPLACE INTO ideas VALUES (?,?)', (item['id'], json.dumps(item)))
            event = {'at': item['updated_at'], 'source': source, 'version': item['version'],
                     'from_stage': old['stage'] if old else None, 'to_stage': item['stage'],
                     'changed': [k for k in FIELDS if not old or old.get(k) != item[k]],
                     'note': activity_note or ('Idea captured' if not old else 'Saved changes')}
            db.execute('INSERT INTO activity (idea_id,data) VALUES (?,?)', (item['id'], json.dumps(event)))
            return item

    def activity(self, ident):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute(
                'SELECT data FROM activity WHERE idea_id=? ORDER BY id DESC', (ident,))]

    def history(self, ident):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute(
                'SELECT data FROM revisions WHERE idea_id=? ORDER BY id DESC', (ident,))]

    def export(self):
        # One read transaction keeps ideas and history consistent during writes.
        with self.connect() as db:
            db.execute('BEGIN')
            items = [self.defaults(json.loads(r[0])) for r in db.execute('SELECT data FROM ideas')]
            result = {'schema': 1, 'exported_at': now(), 'ideas': items}
            for table in ('revisions', 'activity'):
                grouped = {item['id']: [] for item in items}
                for ident, data in db.execute(f'SELECT idea_id,data FROM {table} ORDER BY id DESC'):
                    grouped[ident].append(json.loads(data))
                result[table] = grouped
            return result


def handoff(item):
    lines = [f"# {item['title']}", '', f"Desk ID: {item['id']}", f"Stage: {item['stage']}",
             '', 'Use the StoryFlow workspace editorial profile and writing workflow.',
             'Prepare a draft by default. This export does not authorize publication.', '']
    for key, label in [('format', 'Format'), ('audience', 'Reader'), ('angle', 'Main takeaway'),
                       ('conversation', 'Conversation summary'), ('decisions', 'Decisions'),
                       ('questions', 'Open questions'), ('next_action', 'Next action'),
                       ('chat_reference', 'Chat reference'),
                       ('experience', 'Your observations'), ('sources', 'Sources to verify'),
                       ('notes', 'Editorial notes'), ('target_date', 'Target date (confirm timezone separately)'),
                       ('wordpress_url', 'Publication link'), ('narration', 'Narration status'), ('draft', 'Article draft')]:
        lines.extend([f'## {label}', item.get(key) or 'Not supplied', ''])
    return '\n'.join(lines)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send(self, status, data, mime='application/json', download=None):
        if mime == 'application/json':
            data = json.dumps(data, ensure_ascii=False)
        raw = data.encode() if isinstance(data, str) else data
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if download:
            self.send_header('Content-Disposition', f'attachment; filename="{download}"')
        self.end_headers()
        self.wfile.write(raw)

    def trusted_host(self):
        return self.headers.get('Host', '') in self.server.allowed_hosts

    def do_GET(self):
        if not self.trusted_host():
            return self.send(403, {'error': 'Host not allowed.'})
        path = urlsplit(self.path).path
        if path == '/api/ideas':
            return self.send(200, self.server.store.all())
        if path == '/api/export':
            return self.send(200, self.server.store.export(),
                             download='storyflow-desk-backup.json')
        if path == '/api/profile':
            return self.send(200, {'text': self.server.profile.read_text(encoding='utf-8')})
        if path == '/api/workflow':
            return self.send(200, json.loads((ROOT / 'workflow.json').read_text(encoding='utf-8')))
        if path.startswith('/api/ideas/'):
            parts = path.strip('/').split('/')
            item = next((x for x in self.server.store.all() if x['id'] == parts[2]), None)
            if not item:
                return self.send(404, {'error': 'Idea not found.'})
            if len(parts) == 4 and parts[3] == 'handoff':
                return self.send(200, handoff(item), 'text/markdown; charset=utf-8', f"storyflow-{item['id']}.md")
            if len(parts) == 4 and parts[3] == 'history':
                return self.send(200, self.server.store.history(item['id']))
            if len(parts) == 4 and parts[3] == 'activity':
                return self.send(200, self.server.store.activity(item['id']))
        files = {'/': ('index.html', 'text/html; charset=utf-8'),
                 '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                 '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if path in files:
            filename, mime = files[path]
            return self.send(200, (ROOT / filename).read_bytes(), mime)
        self.send(404, {'error': 'Not found.'})

    def do_POST(self):
        self.mutate()

    def do_PUT(self):
        self.mutate()

    def mutate(self):
        origin = self.headers.get('Origin')
        if (not self.trusted_host() or self.headers.get('X-StoryFlow') != 'desk'
                or (origin and urlsplit(origin).netloc != self.headers.get('Host'))
                or self.headers.get('Sec-Fetch-Site') == 'cross-site'):
            return self.send(403, {'error': 'Use the StoryFlow desk to make changes.'})
        try:
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise ValueError('JSON required.')
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 2_000_000:
                raise ValueError('Request too large or empty.')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Expected an object.')
            path = urlsplit(self.path).path
            if self.command == 'POST' and path == '/api/ideas':
                return self.send(201, self.server.store.save(payload))
            if self.command == 'PUT' and path.startswith('/api/ideas/') and len(path.split('/')) == 4:
                return self.send(200, self.server.store.save(payload, path.split('/')[-1]))
            return self.send(404, {'error': 'Not found.'})
        except RuntimeError as error:
            self.send(409, {'error': str(error)})
        except LookupError as error:
            self.send(404, {'error': str(error)})
        except (ValueError, TypeError) as error:
            self.send(400, {'error': str(error)})


def create_server(port, database, public_host='', profile=None):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.profile = Path(profile) if profile else ROOT.parent / 'editorial-profile.md'
    server.profile.read_text(encoding='utf-8')
    server.store = Store(database)
    actual_port = server.server_address[1]
    server.allowed_hosts = {f'127.0.0.1:{actual_port}', f'localhost:{actual_port}'}
    if public_host:
        server.allowed_hosts.add(public_host)
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8799)
    parser.add_argument('--db', default=str(ROOT.parent / 'state' / 'editorial-desk.sqlite3'))
    parser.add_argument('--profile', type=Path, default=ROOT.parent / 'editorial-profile.md')
    parser.add_argument('--public-host', default=os.environ.get('STORYFLOW_PUBLIC_HOST', ''))
    args = parser.parse_args()
    server = create_server(args.port, args.db, args.public_host, args.profile)
    print(f'Editorial desk: http://127.0.0.1:{server.server_address[1]} (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
