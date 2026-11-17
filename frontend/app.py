import json
import os
from pathlib import Path
import requests
import streamlit as st

API = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')
st.set_page_config(page_title='AgriScheme AI Chat', page_icon='🌾', layout='wide')
css = (Path(__file__).parent / 'style.css').read_text(encoding='utf-8')
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

try:
    res = requests.get(f'{API}/health', timeout=5)
    res.raise_for_status()
    health = res.json()
    online = True
except requests.RequestException:
    health, online = {}, False

with st.sidebar:
    st.title('🌿 AgriScheme AI')
    st.caption('Your agricultural schemes knowledge base')
    st.divider()
    st.subheader('📤 Upload PDF')
    pdf = st.file_uploader('Select a government scheme PDF', type=['pdf'])
    if st.button('🌱 Upload & Index', type='primary', use_container_width=True, disabled=not online or pdf is None):
        if pdf.size > 150 * 1024 * 1024:
            st.error('Maximum file size: 150 MB')
        else:
            with st.spinner('Saving PDF, splitting and embedding...'):
                try:
                    r = requests.post(f'{API}/upload', files={'file': (pdf.name, pdf.getvalue(), 'application/pdf')}, timeout=600)
                    r.raise_for_status()
                    result = r.json()
                    st.success(f'Indexed {result["pages"]} pages / {result["chunks"]} chunks!')
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(f'Upload failed: {exc} — {r.text[:300] if "r" in locals() else ""}')
    st.divider()
    st.metric('PDFs uploaded', health.get('pdf_count', 0))
    st.caption('🟢 Backend online' if online else '🔴 Backend offline')
    st.caption('🟢 FAISS ready' if health.get('has_index') else '⚪ Upload a PDF to create FAISS')
    if st.button('🧹 Clear chat', use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption('Embeddings: Hugging Face (local CPU)')
    st.caption('Answers: ChatOpenAI (API)')

st.markdown('<div class="hero"><h1>🌾 Agricultural Schemes Assistant</h1><p>Ask questions about the government scheme PDFs you uploaded.</p></div>', unsafe_allow_html=True)

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if message.get('sources'):
            with st.expander('📚 PDF Sources'):
                for source in message['sources']:
                    st.markdown(f'**{source["file"]} — Page {source["page"]}**')
                    st.caption(source['snippet'])

question = st.chat_input('Ask about eligibility, benefits, documents...', disabled=not online or not health.get('has_index'))
if question:
    st.session_state.messages.append({'role': 'user', 'content': question})
    with st.chat_message('user'):
        st.markdown(question)
    with st.chat_message('assistant'):
        sources = []
        answer_parts = []
        def token_stream():
            global sources
            with requests.post(f'{API}/ask/stream', json={'question': question}, stream=True, timeout=(10, 180)) as response:
                response.raise_for_status()
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    event = json.loads(line)
                    if event['type'] == 'sources':
                        sources = event['sources']
                    elif event['type'] == 'token':
                        answer_parts.append(event['content'])
                        yield event['content']
                    elif event['type'] == 'error':
                        raise RuntimeError(event['message'])
        try:
            st.write_stream(token_stream())
            if sources:
                with st.expander('📚 PDF Sources'):
                    for source in sources:
                        st.markdown(f'**{source["file"]} — Page {source["page"]}**')
                        st.caption(source['snippet'])
            st.session_state.messages.append({'role': 'assistant', 'content': ''.join(answer_parts), 'sources': sources})
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            st.error(f'Chat failed: {exc}')
