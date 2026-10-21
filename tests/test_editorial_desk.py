import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from webapp.server import create_server


class EditorialDeskTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.server = create_server(0, Path(self.directory.name) / 'desk.db')
        self.url = 'http://127.0.0.1:' + str(self.server.server_address[1])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, path='/api/ideas', payload=None, method=None, headers=None):
        request = Request(self.url + path, data=json.dumps(payload).encode() if payload is not None else None,
                          method=method, headers=headers or {'Content-Type': 'application/json', 'X-StoryFlow': 'desk'})
        with urlopen(request) as response:
            return json.load(response)

    def test_lifecycle_history_export_and_conflict(self):
        item = self.request(payload={'title': 'A real idea'})
        self.assertEqual(item['stage'], 'idea')
        updated = self.request('/api/ideas/' + item['id'], {**item, 'draft': 'My story', 'stage': 'review'}, 'PUT')
        self.assertEqual(self.request()[0]['draft'], 'My story')
        with self.assertRaises(HTTPError) as conflict:
            self.request('/api/ideas/' + item['id'], item, 'PUT')
        self.assertEqual(conflict.exception.code, 409)
        self.assertEqual(len(self.request('/api/ideas/' + item['id'] + '/history')), 1)
        archived = self.request('/api/ideas/' + item['id'], {**updated, 'archived': True}, 'PUT')
        self.assertTrue(archived['archived'])
        restored = self.request('/api/ideas/' + item['id'], {**archived, 'archived': False}, 'PUT')
        self.assertFalse(restored['archived'])
        backup = self.request('/api/export')
        self.assertEqual(backup['ideas'][0]['draft'], 'My story')
        self.assertEqual(len(backup['revisions'][item['id']]), 3)
        with urlopen(self.url + '/api/ideas/' + item['id'] + '/handoff') as response:
            handoff = response.read().decode()
            self.assertIn('My story', handoff)
            self.assertIn('does not authorize publication', handoff)

    def test_invalid_input_and_unconfirmed_publication(self):
        for payload in [{'title': ''}, {'title': 'Test', 'stage': 'fake'},
                        {'title': 'Test', 'stage': 'published'},
                        {'title': 'Test', 'wordpress_url': 'javascript:alert(1)'},
                        {'title': 'Test', 'stage': 'scheduled', 'wordpress_url': 'https://example.com/story'},
                        {'title': 'Test', 'checks': ['bad']}]:
            with self.assertRaises(HTTPError) as error:
                self.request(payload=payload)
            self.assertEqual(error.exception.code, 400)
        self.assertEqual(self.request(), [])

    def test_chat_update_preserves_work_and_records_transition(self):
        item = self.request(payload={'title': 'A conversation', 'draft': 'Existing draft', 'sources': 'Source A'})
        updated = self.request('/api/ideas/' + item['id'], {
            'version': item['version'], 'stage': 'research', 'conversation': 'We chose the reader.',
            'decisions': 'Write for shift supervisors.', 'questions': 'Which example?',
            'next_action': 'Codex: check the claims.', 'update_source': 'chat',
            'activity_note': 'Angle established; beginning research.'}, 'PUT')
        self.assertEqual(updated['draft'], 'Existing draft')
        self.assertEqual(updated['sources'], 'Source A')
        events = self.request('/api/ideas/' + item['id'] + '/activity')
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['source'], 'chat')
        self.assertEqual(events[0]['from_stage'], 'idea')
        self.assertEqual(events[0]['to_stage'], 'research')
        self.assertEqual(self.request('/api/export')['activity'][item['id']], events)
        with self.assertRaises(HTTPError):
            self.request('/api/ideas/' + item['id'], {'version': item['version'], 'stage': 'drafting'}, 'PUT')
        self.assertEqual(len(self.request('/api/ideas/' + item['id'] + '/activity')), 2)

    def test_legacy_records_acquire_conversation_fields_without_losing_draft(self):
        item = self.request(payload={'title': 'Old record', 'draft': 'Keep this'})
        for field in ['conversation', 'decisions', 'questions', 'next_action', 'chat_reference']:
            del item[field]
        with self.server.store.connect() as db:
            db.execute('UPDATE ideas SET data=? WHERE id=?', (json.dumps(item), item['id']))
        read = self.request()[0]
        self.assertEqual(read['conversation'], '')
        updated = self.request('/api/ideas/' + item['id'], {'version': item['version'], 'conversation': 'Recovered context'}, 'PUT')
        self.assertEqual(updated['draft'], 'Keep this')
        self.assertEqual(updated['questions'], '')
        self.assertEqual(len(self.request('/api/workflow')), 7)

    def test_cross_origin_and_rebinding_blocked(self):
        for headers in [{'Content-Type': 'application/json'},
                        {'Content-Type': 'application/json', 'X-StoryFlow': 'desk', 'Origin': 'https://evil.invalid'},
                        {'Content-Type': 'application/json', 'X-StoryFlow': 'desk', 'Host': 'evil.invalid'}]:
            with self.assertRaises(HTTPError) as error:
                self.request(payload={'title': 'Injected'}, headers=headers)
            self.assertEqual(error.exception.code, 403)
        self.assertEqual(self.request(), [])

    def test_static_routes_do_not_expose_database(self):
        for path in ['/state/editorial-desk.sqlite3', '/../README.md', '/server.py']:
            with self.assertRaises(HTTPError) as error:
                self.request(path)
            self.assertEqual(error.exception.code, 404)
        with urlopen(self.url) as response:
            self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
            self.assertIn('Editorial desk', response.read().decode())


if __name__ == '__main__':
    unittest.main()
