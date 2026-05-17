import psycopg2
import json
import os


def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])


def save_story(job_id: str, user_input: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO stories (id, topic, status) VALUES (%s, %s, 'processing')",
                (job_id, user_input)
            )


def update_story(job_id: str, result: dict, status: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            root = result.get('root', {})
            cur.execute(
                """UPDATE stories
                   SET status=%s, root_outlet=%s, root_url=%s,
                       root_headline=%s, root_text=%s, root_dna=%s
                   WHERE id=%s""",
                (
                    status,
                    root.get('outlet'),
                    root.get('url'),
                    root.get('headline'),
                    root.get('text'),
                    json.dumps(root.get('dna', {})),
                    job_id,
                )
            )
            for art in result.get('scored_list', []):
                cur.execute(
                    """INSERT INTO outlet_versions
                         (story_id, outlet, country, url, headline, article_text,
                          dna, drift_score, parent_outlet, language)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        job_id,
                        art['outlet'],
                        art.get('country', 'Unknown'),
                        art.get('url'),
                        art.get('headline'),
                        art.get('text'),
                        json.dumps(art.get('dna', {})),
                        art.get('drift_score', 0),
                        art.get('parent_outlet', 'root'),
                        art.get('language', 'en'),
                    )
                )


def get_story(job_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM stories WHERE id=%s", (job_id,))
            story_row = cur.fetchone()
            if not story_row:
                return None
            cur.execute(
                "SELECT * FROM outlet_versions WHERE story_id=%s ORDER BY drift_score",
                (job_id,)
            )
            version_rows = cur.fetchall()
            return build_story_response(story_row, version_rows)


def build_story_response(story_row, version_rows) -> dict:
    # story_row columns: id, topic, input_url, root_outlet, root_url,
    #                    root_headline, root_text, root_dna, status, created_at
    scored_list = [
        {
            'outlet':        row[2],
            'country':       row[3],
            'url':           row[4],
            'headline':      row[5],
            'text':          row[6],
            'dna':           row[7] or {},
            'drift_score':   row[8],
            'parent_outlet': row[9] or 'root',
            'language':      row[10] or 'en',
        }
        for row in version_rows
        # outlet_versions columns: id, story_id, outlet, country, url, headline,
        #                          article_text, dna, drift_score, parent_outlet, language, crawled_at
    ]
    return {
        'job_id': str(story_row[0]),
        'status': story_row[8],
        'root': {
            'outlet':   story_row[3],
            'url':      story_row[4],
            'headline': story_row[5],
            'dna':      story_row[7] or {},
        },
        'scored_list': scored_list,
        'tree': None,
    }


def get_recent() -> list:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, topic, root_headline, root_outlet, status, created_at
                   FROM stories
                   WHERE status='complete'
                   ORDER BY created_at DESC
                   LIMIT 10"""
            )
            rows = cur.fetchall()
            return [
                {
                    'job_id':    str(r[0]),
                    'topic':     r[1],
                    'headline':  r[2],
                    'outlet':    r[3],
                    'created_at': str(r[5]),
                }
                for r in rows
            ]
