import ipaddress
import os
import re
import socket
import requests
import spacy
from urllib.parse import urlparse

nlp = spacy.load('en_core_web_sm')

GDELT_URL   = 'https://api.gdeltproject.org/api/v2/doc/doc'
NEWSAPI_URL = 'https://newsapi.org/v2/everything'

_ENTITY_LABELS = {'PERSON', 'ORG', 'GPE', 'EVENT', 'NORP'}

# RFC-1918 + loopback + link-local + other reserved ranges that must never be fetched
_BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),   # link-local
    ipaddress.ip_network('0.0.0.0/8'),
    ipaddress.ip_network('100.64.0.0/10'),    # shared address space (RFC 6598)
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
]


def _is_url(text: str) -> bool:
    return text.startswith('http://') or text.startswith('https://')


def _is_safe_url(url: str) -> bool:
    """Return False if the URL's hostname resolves to a private/internal IP (SSRF guard)."""
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return False
        for _, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
            ip = ipaddress.ip_address(sockaddr[0])
            if any(ip in net for net in _BLOCKED_NETWORKS):
                return False
        return True
    except Exception:
        return False


def _outlet_from_url(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    domain = re.sub(r'^www\.', '', domain)
    return domain.split('.')[0].capitalize()


def _fetch_text(url: str) -> str:
    """Fetch raw page text (first 300 words). Blocks private IPs; returns '' on any error."""
    if not _is_safe_url(url):
        return ''
    try:
        r = requests.get(url, timeout=8, headers={'User-Agent': 'StoryTrace/1.0'})
        r.raise_for_status()
        words = r.text.split()[:300]
        return ' '.join(words)
    except Exception:
        return ''


def query_gdelt(query: str) -> dict | None:
    """Return the earliest matching article from GDELT, or None."""
    try:
        r = requests.get(GDELT_URL, params={
            'query':      query,
            'mode':       'artlist',
            'maxrecords': 5,
            'sort':       'DateAsc',   # earliest = root story
            'format':     'json',
        }, timeout=10)
        articles = r.json().get('articles', [])
        return articles[0] if articles else None
    except Exception:
        return None


def query_newsapi(query: str) -> dict | None:
    """Fallback if GDELT returns nothing. Fetches multiple results and picks the earliest."""
    api_key = os.environ.get('NEWSAPI_KEY')
    if not api_key:
        return None
    try:
        r = requests.get(NEWSAPI_URL, params={
            'q':        query,
            'sortBy':   'publishedAt',
            'pageSize': 10,   # fetch batch; pick oldest as the likely root/source article
            'apiKey':   api_key,
        }, timeout=10)
        articles = r.json().get('articles', [])
        if not articles:
            return None
        # NewsAPI returns newest-first; select earliest publishedAt as the root
        return min(articles, key=lambda a: a.get('publishedAt', ''))
    except Exception:
        return None


def _extract_entities(text: str) -> list[str]:
    doc = nlp(text[:1000])  # cap NLP input for speed
    return [e.text for e in doc.ents if e.label_ in _ENTITY_LABELS]


def run(state: dict) -> dict:
    user_input: str = state['input']

    # --- Direct URL input: treat the URL itself as the root story ---
    if _is_url(user_input):
        if not _is_safe_url(user_input):
            state['error'] = f'Rejected URL targeting private/internal host: {user_input}'
            return state
        text = _fetch_text(user_input)
        entities = _extract_entities(text) or [_outlet_from_url(user_input)]
        state['entities'] = entities
        state['root'] = {
            'outlet':    _outlet_from_url(user_input),
            'country':   'US',
            'url':       user_input,
            'headline':  '',
            'text':      text,
            'published': '',
            'dna':       {},
        }
        return state

    # --- Topic input: extract entities then query GDELT → NewsAPI ---
    entities = _extract_entities(user_input)
    query = ' '.join(entities[:3]) if entities else user_input
    state['entities'] = entities if entities else [user_input]

    gdelt_raw = query_gdelt(query)
    newsapi_raw = None if gdelt_raw else query_newsapi(query)
    raw = gdelt_raw or newsapi_raw

    if not raw:
        state['error'] = f'Could not find source story for: {user_input}'
        return state

    if gdelt_raw:
        url = raw.get('url', '')
        state['root'] = {
            'outlet':    raw.get('domain', 'Unknown').split('.')[0].capitalize(),
            'country':   'US',
            'url':       url,
            'headline':  raw.get('title', ''),
            'text':      _fetch_text(url) if url else '',
            'published': raw.get('seendate', ''),
            'dna':       {},
        }
    else:
        url = raw.get('url', '')
        state['root'] = {
            'outlet':    raw.get('source', {}).get('name', 'Unknown'),
            'country':   'US',
            'url':       url,
            'headline':  raw.get('title', ''),
            'text':      raw.get('description', '') or _fetch_text(url),
            'published': raw.get('publishedAt', ''),
            'dna':       {},
        }

    return state
