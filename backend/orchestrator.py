from langgraph.graph import StateGraph, END
from agents import (
    seed_agent, crawler_agent, translator,
    dna_extractor, drift_scorer, geo_builder, alert_agent,
)

# Contract: the Translator mutates state['articles'] in-place (updates art['text'] and
# art['language'] on each dict directly). The DNA Extractor then reads the already-translated
# text from state['articles']. Do NOT have the Translator produce a new list under a
# different key — it must write back into the same list so dna_extractor sees the updates.


def build_pipeline():
    g = StateGraph(dict)

    g.add_node('seed',       seed_agent.run)
    g.add_node('crawler',    crawler_agent.run)
    g.add_node('translator', translator.run)
    g.add_node('dna',        dna_extractor.run)
    g.add_node('scorer',     drift_scorer.run)
    g.add_node('geo',        geo_builder.run)
    g.add_node('alert',      alert_agent.run)

    g.set_entry_point('seed')
    g.add_edge('seed',       'crawler')
    g.add_edge('crawler',    'translator')  # translate before DNA extraction
    g.add_edge('translator', 'dna')
    g.add_edge('dna',        'scorer')
    g.add_edge('scorer',     'geo')
    g.add_edge('geo',        'alert')
    g.add_edge('alert',      END)

    return g.compile()


pipeline = build_pipeline()


def run_pipeline(job_id: str, user_input: str) -> dict:
    initial_state = {
        'job_id': job_id,
        'input':  user_input,
    }
    return pipeline.invoke(initial_state)
