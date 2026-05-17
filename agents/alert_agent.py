import os
import requests

THRESHOLD = 70


def send_alert(payload: dict) -> None:
    webhook = os.environ.get('WEBHOOK_URL', '')
    if webhook:
        try:
            requests.post(webhook, json=payload, timeout=5)
        except Exception:
            pass


def run(state: dict) -> dict:
    alerts_fired = []
    for art in state.get('scored_list', []):
        if art['drift_score'] >= THRESHOLD:
            payload = {
                'job_id':      state.get('job_id'),
                'outlet':      art['outlet'],
                'country':     art.get('country', 'Unknown'),
                'drift_score': art['drift_score'],
                'headline':    art.get('headline', ''),
                'url':         art.get('url', ''),
                'alert':       f"DRIFT ALERT: {art['outlet']} scored {art['drift_score']}/100",
            }
            send_alert(payload)
            alerts_fired.append(art['outlet'])

    state['alerts_fired'] = alerts_fired
    return state
