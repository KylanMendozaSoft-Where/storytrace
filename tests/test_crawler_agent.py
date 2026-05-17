from unittest.mock import MagicMock, patch

from agents.crawler_agent import (
    WORD_CAP,
    entity_match,
    fetch_first_300_words,
    run,
)


def test_entity_match_case_insensitive():
    assert entity_match('Iran Signs Nuclear Deal', ['iran', 'nuclear']) is True
    assert entity_match('Local Weather Update', ['iran']) is False


def test_fetch_first_300_words_caps_at_300():
    long_text = ' '.join(['word'] * 500)
    mock_resp = MagicMock()
    mock_resp.text = long_text
    with patch('agents.crawler_agent.requests.get', return_value=mock_resp):
        result = fetch_first_300_words('https://example.com/article')
    assert result is not None
    assert len(result.split()) <= WORD_CAP


def test_fetch_first_300_words_returns_none_on_exception():
    with patch('agents.crawler_agent.requests.get', side_effect=Exception('timeout')):
        result = fetch_first_300_words('https://example.com/article')
    assert result is None


def _make_feed_entry(title: str, link: str):
    entry = MagicMock()
    entry.get = lambda key, default='': title if key == 'title' else default
    entry.link = link
    entry.title = title
    return entry


def _make_feed(entries):
    feed = MagicMock()
    feed.entries = entries
    return feed


def test_run_returns_articles_for_matched_headlines():
    entry = _make_feed_entry('Iran nuclear talks resume', 'https://bbc.com/iran')
    feed = _make_feed([entry])

    with (
        patch('agents.crawler_agent.feedparser.parse', return_value=feed),
        patch('agents.crawler_agent.fetch_first_300_words', return_value='article body text'),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran', 'nuclear']})

    assert len(state['articles']) == 1
    art = state['articles'][0]
    assert art['outlet'] == 'BBC'
    assert art['url'] == 'https://bbc.com/iran'
    assert art['headline'] == 'Iran nuclear talks resume'
    assert art['text'] == 'article body text'
    assert art['language'] == 'en'


def test_run_skips_feed_when_parser_raises():
    with (
        patch('agents.crawler_agent.feedparser.parse', side_effect=Exception('feed down')),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran']})

    assert state['articles'] == []


def test_run_one_article_per_outlet():
    entries = [
        _make_feed_entry('Iran deal update 1', 'https://bbc.com/1'),
        _make_feed_entry('Iran deal update 2', 'https://bbc.com/2'),
        _make_feed_entry('Iran deal update 3', 'https://bbc.com/3'),
    ]
    feed = _make_feed(entries)

    with (
        patch('agents.crawler_agent.feedparser.parse', return_value=feed),
        patch('agents.crawler_agent.fetch_first_300_words', return_value='body'),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran']})

    assert len(state['articles']) == 1
    assert state['articles'][0]['url'] == 'https://bbc.com/1'


def test_run_skips_when_fetch_returns_none():
    entry = _make_feed_entry('Iran nuclear talks', 'https://bbc.com/iran')
    feed = _make_feed([entry])

    with (
        patch('agents.crawler_agent.feedparser.parse', return_value=feed),
        patch('agents.crawler_agent.fetch_first_300_words', return_value=None),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': ['Iran']})

    assert state['articles'] == []


def test_run_with_no_entities():
    entry = _make_feed_entry('Iran nuclear talks', 'https://bbc.com/iran')
    feed = _make_feed([entry])

    with (
        patch('agents.crawler_agent.feedparser.parse', return_value=feed),
        patch.dict('agents.crawler_agent.RSS_FEEDS', {'BBC': 'http://fake-feed'}, clear=True),
    ):
        state = run({'entities': []})

    assert state['articles'] == []
