"""Generate candidate questions, never observations or a frozen experiment."""
import json
import re
import unicodedata
from urllib.parse import urlsplit
from .paths import repository_root


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().split())


def mentions(text, name):
    # Names can be written with or without spaces/hyphens. ASCII boundaries
    # avoid treating a short brand such as "AI" as the middle of "trail".
    parts = re.findall(r"[^\W_]+", normalized(name), re.UNICODE)
    if not parts:
        return False
    pattern = r"[\W_]*".join(re.escape(x) for x in parts)
    if all(x.isascii() for x in parts):
        pattern = r"(?<![a-z0-9])" + pattern + r"(?![a-z0-9])"
    return bool(re.search(pattern, normalized(text)))


def core_candidates(brief):
    bank = json.loads((repository_root() / 'skills/geo-discover/templates/core-question-library.json').read_text('utf-8'))
    lang = brief['language']
    values = {key: brief.get(key, '') for key in ('brand', 'category', 'site_url')}
    values.update(audience=(brief.get('audiences') or [''])[0], scenario=(brief.get('scenarios') or [''])[0])
    forbidden = [values['brand'], *brief.get('brand_aliases', [])]
    if values['site_url']:
        host = urlsplit(values['site_url']).hostname or ''
        forbidden.append(host)
        if host.startswith('www.'):
            forbidden.append(host[4:])
    candidates, gaps = [], []
    for item in bank['questions']:
        required = item['requires'] + (['brand'] if item['observation_line'] == 'D' else [])
        missing = [key for key in required if not values.get(key)]
        if missing:
            gaps.append({'question_type': item['id'], 'reason': 'Missing inputs: ' + ', '.join(missing)})
            continue
        text = item['text'][lang].format(**values)
        if item['observation_line'] == 'D' and any(mentions(text, x) for x in forbidden if x):
            gaps.append({'question_type': item['id'], 'reason': 'Brand, alias or official domain leaked into the non-brand prompt; rewrite the category/scenario inputs.'})
            continue
        candidates.append({
            'key': item['id'], 'text': text, 'dimension': item['dimension'],
            'question_group': 'core', 'observation_line': item['observation_line'],
            'intent_tag': item['intent_tag'], 'purpose': item['purpose'][lang],
            'judgement': item['judgement'][lang],
        })
    return candidates, gaps
