"""Create a fictional story in an empty, separate demo database."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from webapp.server import Store


def seed(path):
    store = Store(path)
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if any(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
               for table in ('ideas', 'revisions', 'activity')):
            raise ValueError('Demo requires an empty database. Choose a new --db path.')
    item = store.save({
        'title': 'Example: Give unfinished ideas a place to wait',
        'audience': 'Writers with more ideas than writing time',
        'experience': 'Fictional demonstration only; this is not an author testimony.',
        'conversation': 'Explore how a small idea note can make it easier to resume writing.',
        'questions': 'What should the smallest useful idea note contain?',
        'next_action': 'Choose a concrete example.',
        'update_source': 'chat', 'activity_note': 'Example conversation: captured the question.'})
    item = store.save({
        'version': item['version'], 'stage': 'drafting',
        'decisions': 'Use a hypothetical example; make no research claims.',
        'questions': '', 'angle': 'Save a question and a next step, not just a title.',
        'draft': '# Give unfinished ideas a place to wait\n\nImagine noticing a question on a walk. '
                 'You are not ready to write an article, but you can save what made you curious.\n\n'
                 'A useful note might contain three things: the question, why a reader might care, '
                 'and what to explore next.\n\nThe note does not need to be polished. It needs '
                 'to give your future self somewhere to begin.',
        'next_action': 'Read the example draft and improve the opening.',
        'update_source': 'chat', 'activity_note': 'Example conversation: drafted a hypothetical scenario.'}, item['id'])
    return store.save({
        'version': item['version'], 'stage': 'review',
        'conversation': 'An example draft is ready for the author to review.',
        'checks': ['facts', 'structure'],
        'activity_note': 'Example: moved to review, with publication undecided.'}, item['id'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True, type=Path)
    args = parser.parse_args()
    try:
        item = seed(args.db)
    except ValueError as error:
        parser.exit(1, f'{error}\n')
    print(f"Example created: {item['title']} (stage: {item['stage']})")
