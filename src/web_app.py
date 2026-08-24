"""Browser UI for DocuMind, served locally with FastAPI."""

from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from groq import GroqError
from pydantic import BaseModel


app = FastAPI(title="DocuMind")


class QuestionRequest(BaseModel):
    question: str


def run_question(question: str) -> dict[str, object]:
    """Load the AI engine only when a user submits a question."""
    if not question.strip():
        return {"answer": "Please enter a question about the Income-tax Act.", "sections": []}

    try:
        from query_engine import answer_query

        answer, sections = answer_query(question.strip())
        return {"answer": answer, "sections": sections}
    except (GroqError, RuntimeError, ValueError) as error:
        return {"answer": f"Unable to answer: {error}", "sections": []}
    except Exception:
        return {"answer": "The service could not complete this request. Please try again.", "sections": []}


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return PAGE


@app.post("/api/ask")
async def ask(request: QuestionRequest) -> dict[str, object]:
    return await asyncio.to_thread(run_question, request.question)


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DocuMind — Income-tax Act Research</title>
<style>
:root{--ink:#112b46;--muted:#61758a;--teal:#087d73;--teal-dark:#05645d;--paper:#fffdf8;--line:#d8e1e8;--wash:#e9f6f3}*{box-sizing:border-box}body{margin:0;min-height:100vh;color:var(--ink);background:linear-gradient(135deg,#f5f1e8,#eef8f6);font:16px/1.55 Inter,system-ui,sans-serif}main{width:min(1080px,calc(100% - 32px));margin:auto;padding:72px 0 48px}.brand{color:var(--teal);font-weight:800;font-size:.76rem;letter-spacing:.14em}h1{font-family:Georgia,serif;font-size:clamp(2.5rem,6vw,4.5rem);line-height:1;margin:.5rem 0 1rem;letter-spacing:-.045em}.lead{color:var(--muted);max-width:650px;font-size:1.1rem}.grid{display:grid;grid-template-columns:minmax(280px,.85fr) minmax(0,1.3fr);gap:20px;margin-top:38px}.card{background:rgba(255,253,248,.9);border:1px solid var(--line);border-radius:20px;box-shadow:0 16px 50px rgba(17,43,70,.08);padding:24px}label{display:block;font-size:.84rem;font-weight:750;margin-bottom:8px}textarea{resize:vertical;width:100%;min-height:145px;border:1px solid var(--line);border-radius:12px;padding:13px;color:var(--ink);font:inherit;outline:0}textarea:focus{border-color:var(--teal);box-shadow:0 0 0 3px rgba(8,125,115,.14)}button{border:0;border-radius:12px;cursor:pointer;color:white;background:var(--teal);font:700 1rem inherit;margin-top:14px;padding:13px 18px;transition:.18s;width:100%}button:hover{background:var(--teal-dark)}button:disabled{cursor:wait;opacity:.65}.examples{margin-top:22px}.examples p{color:var(--muted);font-size:.85rem;margin:0 0 9px}.example{color:var(--teal-dark);background:var(--wash);font-size:.82rem;margin:0 5px 7px 0;padding:7px 10px;width:auto}.answer-title{display:flex;justify-content:space-between;font-size:.84rem;font-weight:800;text-transform:uppercase}#answer{min-height:245px;margin-top:18px;white-space:pre-wrap}.placeholder{color:var(--muted);display:grid;min-height:220px;place-items:center;text-align:center}.pill{display:inline-block;margin:4px 5px 0 0;padding:4px 9px;color:var(--teal-dark);background:var(--wash);border-radius:999px;font-size:.82rem;font-weight:700}#sources{border-top:1px solid var(--line);margin-top:18px;padding-top:13px}#sources:empty{display:none}.source-label{color:var(--muted);display:block;font-size:.8rem;margin-bottom:4px}footer{color:var(--muted);font-size:.8rem;margin-top:28px;text-align:center}@media(max-width:760px){main{padding-top:48px}.grid{grid-template-columns:1fr}}
</style></head><body><main><div class="brand">LEGAL RESEARCH ASSISTANT</div><h1>DocuMind</h1><p class="lead">Ask grounded questions about the Income-tax Act, 1961. Every answer is generated from retrieved statutory context.</p><section class="grid"><div class="card"><label for="question">Your question</label><textarea id="question" placeholder="For example: What deductions are available under section 80C?"></textarea><button id="ask">Ask DocuMind</button><div class="examples"><p>Try an example</p><button class="example">What is section 1?</button><button class="example">What is agricultural income?</button><button class="example">Explain section 80C.</button></div></div><div class="card"><div class="answer-title"><span>Answer</span><span id="status"></span></div><div id="answer" class="placeholder">Your grounded answer will appear here.</div><div id="sources"></div></div></section><footer>DocuMind is a research aid, not legal advice.</footer></main><script>
const q=document.querySelector('#question'),b=document.querySelector('#ask'),a=document.querySelector('#answer'),s=document.querySelector('#sources'),t=document.querySelector('#status');const safe=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));async function submit(){const text=q.value.trim();if(!text){q.focus();return}b.disabled=true;t.textContent='Searching…';a.className='placeholder';a.textContent='Finding relevant statutory context…';s.innerHTML='';try{const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:text})});if(!r.ok)throw Error();const d=await r.json();a.className='';a.textContent=d.answer;const u=[...new Set(d.sections||[])];s.innerHTML=u.length?'<span class="source-label">Retrieved context</span>'+u.map(x=>'<span class="pill">Section '+safe(x)+'</span>').join(''):''}catch{a.className='';a.textContent='The service could not complete this request. Please try again.'}finally{b.disabled=false;t.textContent=''}}b.addEventListener('click',submit);q.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter')submit()});document.querySelectorAll('.example').forEach(x=>x.addEventListener('click',()=>{q.value=x.textContent;q.focus()}));
</script></body></html>'''


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
