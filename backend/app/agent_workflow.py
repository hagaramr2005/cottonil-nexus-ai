"""Read-only, bounded multi-agent workflow for the Cottonil portfolio demo.

Agents are independently testable Python roles, NOT autonomous LLM workers.
Only the Narrative Agent may invoke the optional Ollama endpoint. Business facts
come from the pre-existing, fixed, read-only Copilot SQL selectors. Neither the
supervisor nor the LLM can issue arbitrary SQL, filesystem or write-tool calls.
"""
from dataclasses import dataclass
from math import isfinite
import re
from typing import Literal

AgentStatus = Literal['completed', 'blocked', 'skipped', 'fallback']

@dataclass(frozen=True)
class Agent:
    id: str
    purpose: str
    tools: tuple[str, ...]

AGENTS = (
    Agent('supervisor', 'Route the user question; never grant permissions.', ()),
    Agent('sales_analyst', 'Read permitted sales metrics and source trust flags.', ('readonly_metrics',)),
    Agent('risk_investigator', 'Read recorded cases and distinguish leads from proven facts.', ('readonly_cases',)),
    Agent('grounding_reviewer', 'Validate evidence, block injection and ungrounded LLM use.', ()),
    Agent('narrative', 'Write a bilingual answer using verified evidence or safe fallback.', ('optional_ollama',)),
)

# This is an allowlist of existing server-side tool functions, not LLM-callable tools.
ALLOWED_READ_TOOLS = frozenset({'readonly_metrics', 'readonly_cases'})
UNTRUSTED_INSTRUCTION = re.compile(
    r'(?i)(ignore (?:all |previous |the )?(?:instructions|rules)|system prompt|developer message|'
    r'reveal (?:secret|token|password)|drop table|\bselect\s+.+\bfrom\b|'
    r'تجاهل التعليمات|اكشف (?:السر|كلمة السر))'
)


def registry():
    """Public metadata. No policy prompts, credentials or user information."""
    return {'architecture': 'bounded-role-based-multi-agent',
            'agents': [{'id': a.id, 'purpose': a.purpose, 'tools': list(a.tools)} for a in AGENTS],
            'llm_roles': ['narrative'], 'read_only': True,
            'note': 'Deterministic specialist agents; not an autonomous multi-LLM swarm.'}


def event(agent_id: str, status: AgentStatus, detail: str):
    return {'agent': agent_id, 'status': status, 'detail': detail}


def sales_analyst(evidence):
    """Enforce provenance and finite numeric values before formatting sales figures."""
    if evidence['type'] != 'metrics':
        return evidence
    from .copilot import ALIASES
    values = evidence['metrics']
    valid = bool(values) and all(
        m.get('key') in ALIASES and isinstance(m.get('value'), (int, float))
        and not isinstance(m.get('value'), bool) and isfinite(m['value'])
        and isinstance(m.get('source'), str) and bool(m['source'].strip())
        and m['source'] in evidence['sources']
        and m.get('trust') in ('trusted', 'warning', 'blocked', 'verified', 'unverified', 'partial', 'available', 'review', 'unknown')
        for m in values
    )
    if not valid:
        return {'type': 'unsupported', 'cases': [], 'metrics': [], 'sources': [],
                'limitations': ['Metric provenance or trust metadata is incomplete; no figures were released.']}
    return evidence


def risk_investigator(evidence):
    """No fictional investigations when the store contains no proven lead records."""
    if evidence['type'] not in ('risks', 'case'):
        return evidence
    if not evidence['cases']:
        return {'type': 'no_cases', 'cases': [], 'metrics': [], 'sources': [],
                'limitations': ['No investigation cases are recorded.']}
    if any(not isinstance(c.get('id'), str) or not c.get('id') or not c.get('title') for c in evidence['cases']):
        return {'type': 'unsupported', 'cases': [], 'metrics': [], 'sources': [],
                'limitations': ['Case evidence was incomplete.']}
    return evidence


def run(question: str, language: str, page: str, case_id: str | None, history):
    """Run sequential bounded specialist roles. Caller must enforce RBAC first."""
    from . import copilot
    trace = [event('supervisor', 'completed', 'Bounded read-only route chosen.')]
    common = {'language': language, 'llm_model': copilot.os.getenv('NEXUS_LLM_MODEL') or None}
    def response(answer, evidence, mode, *, reason=None, generated=False):
        return {**common, 'mode': mode, 'llm_available': generated, 'llm_used': generated,
                'answer': answer, 'sources': evidence.get('sources', []),
                'metrics': evidence.get('metrics', []), 'cases': evidence.get('cases', []),
                'limitations': evidence.get('limitations', []), 'llm_reason': reason,
                'agent_trace': trace}
    empty = {'type': 'conversation', 'sources': [], 'metrics': [], 'cases': [], 'limitations': []}
    if copilot.TO_AR.search(question) or copilot.TO_EN.search(question):
        text = ('أكيد، هكمل معاك بالعربي. اسألني عن بيانات Cottonil أو التحقيقات المسجلة.' if language == 'ar' else
                "Of course. I'll continue in English. Ask me about recorded Cottonil data or investigations.")
        trace.append(event('narrative', 'completed', 'Localized conversational response; no tools called.'))
        return response(text, empty, 'conversational')
    if copilot.GREET_AR.match(question) or copilot.GREET_EN.match(question):
        text = ('أهلًا! أقدر أساعدك في تحليل مبيعات Cottonil، المخاطر التجارية، أداء الفروع، والبيانات المتاحة. تحب نبدأ بإيه؟' if language == 'ar' else
                'Hello! I can help you explore Cottonil sales, business risks, branch performance and available evidence. What would you like to investigate?')
        trace.append(event('narrative', 'completed', 'Localized greeting; no tools called.'))
        return response(text, empty, 'conversational')

    # The evidence selector uses only pre-defined parameterized SQL. It does not
    # execute text, SQL, tool names or commands from the model or client.
    evidence = copilot.select_evidence(question, page, case_id, history, language)
    kind = evidence['type']
    if kind == 'metrics':
        evidence = sales_analyst(evidence)
        trace.append(event('sales_analyst', 'completed' if evidence['type'] == kind else 'blocked',
                           'Metric source and trust checked.' if evidence['type'] == kind else 'Invalid metric provenance.'))
    elif kind in ('risks', 'case'):
        evidence = risk_investigator(evidence)
        trace.append(event('risk_investigator', 'completed' if evidence['type'] == kind else 'blocked',
                           'Recorded case evidence checked.' if evidence['type'] == kind else 'No valid recorded cases.'))
    else:
        trace.append(event('sales_analyst', 'skipped', 'Not a metrics request.'))
        trace.append(event('risk_investigator', 'skipped', 'Not a case request.'))
    fallback = copilot.fallback_answer(evidence, language, question)
    injection = bool(UNTRUSTED_INSTRUCTION.search(question))
    if injection:
        evidence = {**evidence, 'limitations': evidence['limitations'] + ['Potential prompt injection: LLM call skipped.']}
    no_llm = injection or evidence['type'] in ('unsupported', 'no_data', 'no_cases', 'clarify') or any(
        term in question.casefold() for term in copilot.FINANCIAL_LOSS)
    trace.append(event('grounding_reviewer', 'blocked' if no_llm else 'completed',
                       'LLM blocked: unsafe or insufficient evidence.' if no_llm else 'Evidence is eligible for a read-only explanation.'))
    if no_llm:
        trace.append(event('narrative', 'fallback', 'Evidence-only deterministic response.'))
        return response(fallback, evidence, 'deterministic-fallback')
    # ONLY the Narrative agent is permitted to call the optional model. The
    # provider has no tools / SQL / write API and cannot change the evidence.
    generated, reason = copilot.llm_explain(question, evidence, language, history)
    trace.append(event('narrative', 'completed' if generated else 'fallback',
                       'Ollama-assisted explanation.' if generated else 'Model unavailable or output rejected.'))
    return response(generated or fallback, evidence,
                    'grounded-llm' if generated else 'deterministic-fallback',
                    reason=reason, generated=bool(generated))
