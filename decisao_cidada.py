import streamlit as st
from groq import Groq
from datetime import datetime
import json
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="DECISÃO CIDADÃ", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');

    .stApp { background-color: #FFFFFF; color: #000000; font-family: 'DM Sans', sans-serif; }
    [data-testid="stSidebar"] { display: none; }

    .stTextInput>div>div>input,
    .stTextArea>div>textarea,
    .stSelectbox>div>div>div {
        background-color: #F0FDFA !important;
        color: #000000 !important;
        border: 1px solid #0D9488 !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background: linear-gradient(135deg, #115E59, #0D9488) !important;
        color: white !important; font-weight: 600; border: none;
        box-shadow: 2px 2px 8px rgba(17,94,89,0.25);
        font-family: 'DM Sans', sans-serif !important;
        transition: all 0.2s ease;
    }
    .stButton>button *, .stButton>button p { color: white !important; }
    .stButton>button:hover { background: linear-gradient(135deg, #134E4A, #115E59) !important; transform: translateY(-1px); }

    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #1A1A2E !important; }
    p, span, label, div { color: #1A1A2E !important; font-family: 'DM Sans', sans-serif; }

    .card {
        background: linear-gradient(135deg, #F0FDFA 0%, #CCFBF1 100%);
        padding: 22px; border-radius: 16px;
        border: 1px solid #0D9488; margin-bottom: 15px;
        color: #1A1A2E; box-shadow: 0 2px 12px rgba(17,94,89,0.08);
        white-space: pre-wrap;
    }
    .card-dark {
        background: linear-gradient(135deg, #042F2E 0%, #022C22 100%);
        padding: 22px; border-radius: 16px;
        border: 1px solid #0D9488; margin-bottom: 15px;
        white-space: pre-wrap;
    }
    .card-dark, .card-dark * { color: #99F6E4 !important; }

    .card-blue { background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); padding: 22px; border-radius: 16px; border: 1px solid #93C5FD; margin-bottom: 15px; white-space: pre-wrap; }
    .card-orange { background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); padding: 22px; border-radius: 16px; border: 1px solid #FDBA74; margin-bottom: 15px; white-space: pre-wrap; }
    .card-purple { background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); padding: 22px; border-radius: 16px; border: 1px solid #C4B5FD; margin-bottom: 15px; white-space: pre-wrap; }

    .badge { background: #115E59; color: white !important; padding: 4px 14px; border-radius: 20px; font-size: 0.78em; font-weight: 600; display: inline-block; margin: 2px; }
    .badge-verde { background: #059669; color: white !important; padding: 4px 14px; border-radius: 20px; font-size: 0.78em; font-weight: 600; display: inline-block; margin: 2px; }

    .stat-box { background: #F0FDFA; border-radius: 12px; padding: 18px; text-align: center; border: 1px solid #0D9488; }
    .stat-numero { font-size: 2em; font-weight: 700; color: #115E59 !important; font-family: 'Playfair Display', serif; }

    .hist-item { background: #F0FDFA; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; border-left: 4px solid #0D9488; }

    .perfil-btn>button { background: linear-gradient(135deg, #115E59, #0D9488) !important; color: white !important; font-weight: 700 !important; border-radius: 12px !important; height: 3em !important; }
    .perfil-btn>button *, .perfil-btn>button p { color: white !important; }

    .checklist-item { background:#FFFFFF; border:1px solid #99F6E4; border-radius:10px; padding: 10px 16px; margin-bottom:6px; }

    .disclaimer-topo {
        background: #F0FDFA; border: 2px solid #0D9488; border-radius: 12px;
        padding: 14px 18px; font-size: 0.85em; color: #134E4A; margin-bottom: 16px; line-height: 1.6;
    }
    .disclaimer { background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 12px 16px; font-size: 0.8em; color: #92400E; margin-top: 14px; line-height: 1.6; }

    .divider { border: none; height: 1px; background: linear-gradient(to right, transparent, #0D9488, transparent); margin: 20px 0; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CACHE
# ─────────────────────────────────────────────
@st.cache_resource
def get_cache_cidada():
    return {"perfis": {}}

_cache = get_cache_cidada()

# ─────────────────────────────────────────────
# PERSISTÊNCIA LOCAL (JSON)
# ─────────────────────────────────────────────
CHAVES_SALVAR = ['usuario', 'historico_consultas', 'consultas_salvas', 'checklist_voto']

def gerar_json_sessao() -> str:
    dados = {k: st.session_state.get(k) for k in CHAVES_SALVAR}
    dados['salvo_em'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    return json.dumps(dados, ensure_ascii=False, indent=2, default=str)

def carregar_json_sessao(dados: dict):
    for k in CHAVES_SALVAR:
        if k in dados:
            st.session_state[k] = dados[k]

def salvar_perfil_cache(usuario: str):
    _cache["perfis"][usuario] = {k: st.session_state.get(k) for k in CHAVES_SALVAR}

def perfis_salvos() -> list:
    return list(_cache["perfis"].keys())

def carregar_perfil_cache(usuario: str) -> dict | None:
    return _cache["perfis"].get(usuario)

def salvar_consulta(modulo: str, tema: str, conteudo: str):
    st.session_state.historico_consultas.append({
        'data': datetime.now().strftime('%d/%m %H:%M'), 'modulo': modulo, 'tema': tema, 'conteudo': conteudo,
    })

# --- INICIALIZAÇÃO DE ESTADO ---
defaults = {
    'etapa': "Login", 'usuario': "", 'api_key': "", 'pagina': "Home",
    'historico_consultas': [], 'consultas_salvas': [], 'checklist_voto': {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- PRINCÍPIO DE NEUTRALIDADE — compartilhado em todo prompt ---
PRINCIPIO_NEUTRALIDADE = """
PRINCÍPIO OBRIGATÓRIO DE NEUTRALIDADE — siga isso em TODA resposta:
- Você NUNCA recomenda em quem votar, qual partido apoiar, ou qual posição política "correta" adotar
- Para qualquer tema com mais de uma perspectiva legítima, APRESENTE SEMPRE pelo menos duas visões diferentes,
  de forma equilibrada, sem indicar qual é "melhor" ou "certa"
- Use linguagem de mecanismo, não de julgamento: explique COMO algo funciona e QUAIS são os argumentos de cada lado,
  nunca afirme qual argumento é mais válido
- Não tome posição sobre temas controversos atuais — apresente o debate, não vença o debate
- Trate conceitos técnicos (economia, direito constitucional, funcionamento do governo) de forma factual e didática —
  isso não é opinião, é mecanismo institucional
- Você não tem acesso a notícias em tempo real nem a dados eleitorais atualizados — não invente nomes de políticos,
  resultados de eleições ou status de projetos de lei específicos
- Se a pessoa pedir uma opinião direta sobre qual posição é "certa", explique educadamente que seu papel é ajudar
  a entender os argumentos de cada lado, não dizer qual escolher
- Português do Brasil, tom didático e respeitoso
"""

DISCLAIMER_PADRAO = """
<div class="disclaimer">
⚠️ <strong>Importante:</strong> este conteúdo é educativo e busca apresentar múltiplas perspectivas de forma equilibrada —
não representa uma posição política do app nem indica como você deve pensar ou votar. A IA não tem acesso a dados em
tempo real, então para fatos atuais específicos (propostas em tramitação, resultados eleitorais, etc), consulte fontes
oficiais e atualizadas.
</div>
"""

# --- MOTOR DE IA ---
def cidada_ia(prompt: str, system_extra: str = "") -> str:
    try:
        client = Groq(api_key=st.session_state.api_key)
        system = f"""Você é um consultor de educação cívica, especializado em explicar política, economia e
funcionamento do governo de forma clara e imparcial.
Usuário: {st.session_state.usuario}.
{PRINCIPIO_NEUTRALIDADE}
{system_extra}"""
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Erro na API: {e}"

# --- BARRA DE SALVAR ---
def barra_salvar():
    salvar_perfil_cache(st.session_state.usuario)
    nome_usuario = st.session_state.usuario.lower().replace(' ', '_') or 'minha_sessao'
    total = len(st.session_state.historico_consultas)
    salvos = len(st.session_state.consultas_salvas)

    col_info, col_btn = st.columns([4, 2])
    with col_info:
        st.markdown(
            f"<div style='background:#F0FDFA;border:1px solid #0D9488;border-radius:10px;"
            f"padding:10px 14px;font-size:0.84em;color:#1A1A2E;line-height:1.6;'>"
            f"💾 <strong>Antes de sair, salve seus dados no computador.</strong><br>"
            f"<span style='color:#888;font-size:0.88em;'>{total} consultas geradas · {salvos} salvas</span>"
            f"</div>", unsafe_allow_html=True
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("💾 SALVAR MEUS DADOS (.json)", data=gerar_json_sessao(),
            file_name=f"decisao_cidada_{nome_usuario}.json", mime="application/json", use_container_width=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# --- PARSER E RENDERIZADOR DA ANÁLISE CRÍTICA ENRIQUECIDA ---
def _extrair_secao(texto: str, marcador: str) -> str:
    """Extrai o conteúdo entre ###MARCADOR### e o próximo ### ou fim do texto."""
    padrao = rf'###{marcador}###\s*(.*?)(?=###|\Z)'
    m = re.search(padrao, texto, re.DOTALL)
    return m.group(1).strip() if m else ""

def renderizar_analise_critica(texto: str):

    # ── TABELA DE AFIRMAÇÕES ──
    sec_tabela = _extrair_secao(texto, "TABELA_AFIRMACOES")
    linhas_tabela = [l.strip() for l in sec_tabela.split('\n') if '|' in l]

    st.markdown("### 📋 Classificação das afirmações")
    if linhas_tabela:
        cores_tipo = {
            "Promessa": "#3B82F6", "Objetivo político": "#8B5CF6", "Meta condicionada": "#F59E0B",
            "Princípio administrativo": "#6B7280", "Opinião": "#EC4899", "Fato verificável": "#059669",
            "Depende de terceiros": "#DC2626",
        }
        linhas_html = ""
        for linha in linhas_tabela:
            partes = [p.strip() for p in linha.split('|')]
            if len(partes) >= 2:
                afirm, tipo = partes[0], partes[1]
                cor = cores_tipo.get(tipo, "#0D9488")
                linhas_html += f"""<tr>
                    <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;">{afirm}</td>
                    <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;"><span style="background:{cor};color:white;padding:3px 10px;border-radius:12px;font-size:0.82em;">{tipo}</span></td>
                </tr>"""
        st.markdown(f"""
        <table style="width:100%;border-collapse:collapse;background:white;border-radius:10px;overflow:hidden;border:1px solid #E5E7EB;">
        <tr style="background:#F0FDFA;"><th style="padding:8px 12px;text-align:left;">Afirmação</th><th style="padding:8px 12px;text-align:left;">Tipo</th></tr>
        {linhas_html}
        </table>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── GRAU DE OBJETIVIDADE (estrelas) ──
    sec_obj = _extrair_secao(texto, "GRAU_OBJETIVIDADE")
    def _pega_valor(secao, chave, default=0):
        m = re.search(rf'{chave}:\s*(\d+(?:[.,]\d+)?)', secao)
        if not m:
            return default
        valor_str = m.group(1).replace(',', '.')
        valor_float = float(valor_str)
        # Retorna int quando o valor é inteiro, float (1 decimal) quando tem casas decimais
        return round(valor_float) if valor_float == int(valor_float) else round(valor_float, 1)
    def _pega_texto(secao, chave):
        m = re.search(rf'{chave}:\s*(.+)', secao)
        return m.group(1).strip() if m else ""

    muito_esp = int(round(_pega_valor(sec_obj, "muito_especifico")))
    mod_esp = int(round(_pega_valor(sec_obj, "moderadamente_especifico")))
    generico = int(round(_pega_valor(sec_obj, "generico")))
    # Limita entre 0 e 5 — proteção contra valores fora da escala
    muito_esp, mod_esp, generico = max(0,min(5,muito_esp)), max(0,min(5,mod_esp)), max(0,min(5,generico))
    justificativa_obj = _pega_texto(sec_obj, "justificativa")

    def _estrelas(n, total=5):
        return "⭐" * n + "☆" * (total - n)

    st.markdown("### 📊 Grau de objetividade")
    col_o1, col_o2, col_o3 = st.columns(3)
    col_o1.markdown(f"<div class='card' style='text-align:center;padding:14px;'><div style='font-size:0.8em;color:#666;'>Muito específico</div><div style='font-size:1.3em;'>{_estrelas(muito_esp)}</div></div>", unsafe_allow_html=True)
    col_o2.markdown(f"<div class='card' style='text-align:center;padding:14px;'><div style='font-size:0.8em;color:#666;'>Moderadamente específico</div><div style='font-size:1.3em;'>{_estrelas(mod_esp)}</div></div>", unsafe_allow_html=True)
    col_o3.markdown(f"<div class='card' style='text-align:center;padding:14px;'><div style='font-size:0.8em;color:#666;'>Genérico</div><div style='font-size:1.3em;'>{_estrelas(generico)}</div></div>", unsafe_allow_html=True)
    if justificativa_obj:
        st.markdown(f"<div class='card-orange'><strong>Justificativa:</strong><br>{justificativa_obj}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TÉCNICAS DE PERSUASÃO ──
    sec_tec = _extrair_secao(texto, "TECNICAS_PERSUASAO")
    linhas_tec = [l.strip() for l in sec_tec.split('\n') if l.strip()]
    st.markdown("### 🎭 Técnicas de persuasão")
    tec_html = ""
    for linha in linhas_tec:
        if linha.upper().startswith("SIM:"):
            tec_html += f"<div class='checklist-item'>✅ {linha[4:].strip()}</div>"
        elif linha.upper().startswith("NAO:") or linha.upper().startswith("NÃO:"):
            tec_html += f"<div class='checklist-item' style='opacity:0.5;'>⬜ {linha[4:].strip()}</div>"
    if tec_html:
        st.markdown(tec_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── O QUE FALTA PARA AVALIAR ──
    sec_falta = _extrair_secao(texto, "FALTA_PARA_AVALIAR")
    perguntas_falta = [l.strip().lstrip('-•').strip() for l in sec_falta.split('\n') if l.strip()]
    if perguntas_falta:
        st.markdown("### 📈 O que falta para avaliar melhor")
        st.markdown("<div class='card'>" + "<br>".join(f"• {p}" for p in perguntas_falta) + "</div>", unsafe_allow_html=True)

    # ── BENEFÍCIOS E DESAFIOS — lado a lado ──
    sec_benef = _extrair_secao(texto, "BENEFICIOS_POTENCIAIS")
    sec_desaf = _extrair_secao(texto, "DESAFIOS_POTENCIAIS")
    benef_linhas = [l.strip() for l in sec_benef.split('\n') if l.strip()]
    desaf_linhas = [l.strip() for l in sec_desaf.split('\n') if l.strip()]

    col_b, col_d = st.columns(2)
    with col_b:
        st.markdown("#### ⚖️ Possíveis benefícios")
        if benef_linhas:
            st.markdown("<div class='card-blue'>" + "<br>".join(benef_linhas) + "</div>", unsafe_allow_html=True)
    with col_d:
        st.markdown("#### ⚠️ Possíveis desafios")
        if desaf_linhas:
            st.markdown("<div class='card-orange'>" + "<br>".join(desaf_linhas) + "</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── VERIFICABILIDADE (barras) ──
    sec_verif = _extrair_secao(texto, "VERIFICABILIDADE")
    pode_medir = _pega_valor(sec_verif, "pode_ser_medido")
    tem_metas = _pega_valor(sec_verif, "tem_metas")
    tem_prazo = _pega_valor(sec_verif, "tem_prazo")
    tem_numeros = _pega_valor(sec_verif, "tem_numeros")

    st.markdown("### 🔍 Grau de verificabilidade")
    for label, valor in [("Pode ser medido?", pode_medir), ("Tem metas?", tem_metas), ("Tem prazo?", tem_prazo), ("Tem números?", tem_numeros)]:
        cor = "#059669" if valor >= 60 else ("#F59E0B" if valor >= 30 else "#EF4444")
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:0.85em;font-weight:600;"><span>{label}</span><span>{valor}%</span></div>
            <div style="background:#E2E8F0;border-radius:999px;height:10px;overflow:hidden;"><div style="height:100%;border-radius:999px;background:{cor};width:{valor}%;"></div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── VIÉS EMOCIONAL ──
    sec_vies = _extrair_secao(texto, "VIES_EMOCIONAL")
    linhas_vies = [l.strip() for l in sec_vies.split('\n') if l.strip()]
    st.markdown("### 🧠 Viés emocional")
    cores_intensidade = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}
    vies_html = ""
    for linha in linhas_vies:
        if linha.upper().startswith("NOTA:"):
            vies_html += f"<div style='font-style:italic;color:#666;margin-top:6px;'>{linha[5:].strip()}</div>"
        elif ':' in linha:
            emocao, intensidade = linha.split(':', 1)
            emocao, intensidade = emocao.strip(), intensidade.strip()
            icone = cores_intensidade.get(intensidade, "⚪")
            vies_html += f"<span class='badge' style='background:#0D9488;'>{icone} {emocao} ({intensidade})</span> "
    if vies_html:
        st.markdown(f"<div class='card'>{vies_html}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PERGUNTAS JORNALÍSTICAS ──
    sec_perg = _extrair_secao(texto, "PERGUNTAS_JORNALISTICAS")
    perguntas_jorn = [l.strip().lstrip('-•').strip() for l in sec_perg.split('\n') if l.strip()]
    if perguntas_jorn:
        st.markdown("### 🎯 Perguntas inteligentes sobre este texto")
        st.markdown("<div class='card-dark'>" + "<br><br>".join(f"❓ {p}" for p in perguntas_jorn) + "</div>", unsafe_allow_html=True)

    # ── CONCEITOS CITADOS ──
    sec_conceitos = _extrair_secao(texto, "CONCEITOS_CITADOS")
    linhas_conceitos = [l.strip() for l in sec_conceitos.split('\n') if '|' in l]
    if linhas_conceitos:
        st.markdown("### 📚 Conceitos citados")
        for linha in linhas_conceitos:
            partes = [p.strip() for p in linha.split('|')]
            if len(partes) >= 2:
                st.markdown(f"<div class='checklist-item'>📖 <strong>{partes[0]}</strong> — {partes[1]}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── NOTAS FINAIS ──
    sec_notas = _extrair_secao(texto, "NOTAS_FINAIS")
    clareza = _pega_valor(sec_notas, "clareza")
    especificidade = _pega_valor(sec_notas, "especificidade")
    detalhamento = _pega_valor(sec_notas, "detalhamento")
    verificabilidade = _pega_valor(sec_notas, "verificabilidade")
    viabilidade_txt = _pega_texto(sec_notas, "viabilidade")

    st.markdown("### ⭐ Notas Finais")
    c1, c2, c3, c4 = st.columns(4)
    for col, label, val in zip([c1,c2,c3,c4], ["Clareza","Especificidade","Detalhamento","Verificabilidade"], [clareza, especificidade, detalhamento, verificabilidade]):
        cor = "#059669" if val >= 7 else ("#F59E0B" if val >= 4 else "#EF4444")
        col.markdown(f"<div class='stat-box'><div class='stat-numero' style='color:{cor} !important;'>{val}/10</div><div>{label}</div></div>", unsafe_allow_html=True)
    if viabilidade_txt:
        st.markdown(f"<div class='card' style='margin-top:10px;'>🎯 <strong>Viabilidade:</strong> {viabilidade_txt}</div>", unsafe_allow_html=True)

# ============================================================
# TELA: LOGIN
# ============================================================
if st.session_state.etapa == "Login":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🗳️ DECISÃO CIDADÃ")
        st.markdown("**Consultor de Educação Cívica — entenda política, economia e governo para formar sua própria opinião**")

        st.markdown("""<div style="background:#F0FDFA;border:1px solid #0D9488;border-radius:10px;
        padding:10px 16px;margin:10px 0 16px 0;font-size:0.88em;color:#1A1A2E;line-height:1.6;">
        🔒 <strong>ACESSO RESTRITO A CLIENTES DO QUIZ COM PRÊMIOS</strong><br>
        🔗 <a href="https://quizcompremios.com.br/" target="_blank"
        style="color:#115E59;font-weight:600;text-decoration:none;">quizcompremios.com.br</a>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="disclaimer-topo">
        ⚖️ <strong>Este app não diz em quem votar.</strong> Ele existe para ajudar você a entender melhor os temas
        de política, economia e cidadania — sempre apresentando múltiplas perspectivas — para que você forme sua
        própria opinião com mais informação.
        </div>""", unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        perfis = perfis_salvos()
        if perfis:
            st.markdown("#### 🗳️ Decisão Cidadã — clique para acessar seus dados")
            chave_rapida = st.text_input("🔑 Sua Chave API da Groq:", type="password", key="chave_rapida")
            for nome_p in perfis:
                dados_p = carregar_perfil_cache(nome_p)
                total_p = len(dados_p.get('historico_consultas', [])) if dados_p else 0
                st.markdown('<div class="perfil-btn">', unsafe_allow_html=True)
                if st.button(f"🗳️ {nome_p}  —  {total_p} consultas geradas", key=f"perfil_{nome_p}", use_container_width=True):
                    if not chave_rapida.strip():
                        st.warning("Cole sua chave API acima antes de entrar.")
                    else:
                        st.session_state.usuario = nome_p
                        st.session_state.api_key = chave_rapida
                        carregar_json_sessao(dados_p)
                        st.session_state.etapa = "App"
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("**Ou entre com outro nome:**")

        nome  = st.text_input("Seu Nome:")
        chave = st.text_input("Sua Chave API da Groq:", type="password", key="chave_nova")

        if not perfis:
            st.markdown("""<div style="background:#F0FDFA;border:1px solid #0D9488;border-radius:10px;
            padding:12px 16px;font-size:0.86em;color:#1A1A2E;line-height:1.7;margin:10px 0;">
            📥 <strong>Seus dados sumiram?</strong> Selecione abaixo o arquivo <strong>.json</strong> que você salvou antes.
            </div>""", unsafe_allow_html=True)
            arq_login = st.file_uploader("Carregar meus dados salvos (.json):", type=["json"], key="upload_login")
        else:
            arq_login = None

        dados_login = None
        if arq_login is not None:
            try:
                dados_login = json.load(arq_login)
                st.success(f"✅ Dados de **{dados_login.get('usuario','')}** reconhecidos! Clique em Entrar.")
            except Exception:
                st.error("Arquivo inválido.")
                dados_login = None

        if st.button("✨ ENTRAR E APRENDER"):
            if nome and chave:
                st.session_state.usuario = nome
                st.session_state.api_key = chave
                if dados_login:
                    carregar_json_sessao(dados_login)
                st.session_state.etapa = "App"
                st.rerun()
            else:
                st.warning("Preencha nome e chave API.")

        st.markdown("🔑 Não tem chave Groq? Crie grátis em <a href='https://console.groq.com/keys' target='_blank' style='color:#115E59;font-weight:600;'>console.groq.com/keys</a>", unsafe_allow_html=True)

# ============================================================
# TELA: APP
# ============================================================
elif st.session_state.etapa == "App":

    barra_salvar()

    st.markdown("""<div class="disclaimer-topo">
    ⚖️ <strong>Este app é imparcial e educativo.</strong> Sempre apresenta múltiplas perspectivas — nunca diz em quem
    votar ou qual posição é "certa".
    </div>""", unsafe_allow_html=True)

    cols = st.columns(8)
    paginas_nav = [("🏠","Home"),("💰","Economia"),("🏛️","Governo"),("📜","Leis"),("🎓","Aprenda"),("🧠","Critico"),("✅","Checklist"),("📚","Biblioteca")]
    labels_nav = {"Home":"Painel Principal","Economia":"Economia em Linguagem Simples","Governo":"Como Funciona o Governo",
                  "Leis":"Tradutor de Leis","Aprenda":"Aprenda Política","Critico":"Pensamento Crítico",
                  "Checklist":"Antes de Votar","Biblioteca":"Biblioteca de Consultas"}
    for i,(icone,pag) in enumerate(paginas_nav):
        if cols[i].button(icone, key=f"nav_{pag}", help=labels_nav[pag]):
            st.session_state.pagina = pag
            st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ========================
    # HOME
    # ========================
    if st.session_state.pagina == "Home":
        col_u, col_r = st.columns([3, 1])
        with col_u:
            st.title(f"Olá, {st.session_state.usuario}! 🗳️")
            st.markdown("<span class='badge'>Educação Cívica</span>", unsafe_allow_html=True)
        with col_r:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚪 Sair"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

        if len(st.session_state.historico_consultas) == 0:
            st.markdown("""<div style="background:#FEF3C7;border:2px solid #F59E0B;border-radius:12px;
            padding:12px 18px;margin-bottom:4px;color:#000;font-size:0.9em;font-weight:600;">
            ⚠️ Seus dados não estão mais no servidor.
            </div>""", unsafe_allow_html=True)
            arq_home = st.file_uploader("Carregar meus dados salvos (.json):", type=["json"], key="upload_home")
            if arq_home is not None:
                try:
                    dados_home = json.load(arq_home)
                    carregar_json_sessao(dados_home)
                    salvar_perfil_cache(st.session_state.usuario)
                    st.success("✅ Dados recuperados!")
                    st.rerun()
                except Exception:
                    st.error("Arquivo inválido.")
            st.markdown("<br>", unsafe_allow_html=True)

        modulos_count = {}
        for c in st.session_state.historico_consultas:
            modulos_count[c['modulo']] = modulos_count.get(c['modulo'], 0) + 1

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='stat-box'><div class='stat-numero'>{len(st.session_state.historico_consultas)}</div><div>Consultas geradas</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='stat-box'><div class='stat-numero'>{len(st.session_state.consultas_salvas)}</div><div>Salvas</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='stat-box'><div class='stat-numero'>{len(modulos_count)}</div><div>Tópicos explorados</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='stat-box'><div class='stat-numero'>{sum(1 for v in st.session_state.checklist_voto.values() if v)}</div><div>Itens do checklist</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='card'>💡 <em>'Uma democracia saudável depende de cidadãos que pensam por si mesmos — não de cidadãos que pensam igual.'</em></div>", unsafe_allow_html=True)

        st.markdown("### 🗺️ O que cada módulo faz")
        guia = {
            "💰 Economia": "Inflação, juros, dívida pública, impostos, PIB — explicados em linguagem simples",
            "🏛️ Governo": "Como funcionam os 3 poderes e os cargos — prefeito, governador, deputado, senador...",
            "📜 Leis": "Cole uma lei ou trecho legal e receba a tradução em português simples",
            "🎓 Aprenda Política": "Pequenas aulas sobre democracia, federalismo, reforma tributária e mais",
            "🧠 Pensamento Crítico": "Identifique vieses, falácias e manipulação emocional em qualquer texto ou discurso",
            "✅ Antes de Votar": "Checklist para organizar sua pesquisa antes de decidir o voto",
            "📚 Biblioteca": "Histórico de tudo que você já consultou",
        }
        for aba, desc in guia.items():
            st.markdown(f"**{aba}** — {desc}")

        if st.session_state.historico_consultas:
            st.markdown("### 🕐 Últimas Consultas")
            for item in reversed(st.session_state.historico_consultas[-4:]):
                st.markdown(f"<div class='hist-item'><span class='badge'>{item['modulo']}</span> <small style='color:#888'>{item['data']}</small><br><small>{item['tema'][:80]}</small></div>", unsafe_allow_html=True)

    # ========================
    # ECONOMIA
    # ========================
    elif st.session_state.pagina == "Economia":
        st.header("💰 Economia em Linguagem Simples")
        st.markdown("Entenda os conceitos econômicos que aparecem no noticiário todos os dias.")

        tema_economia = st.selectbox("Escolha um tema:", key="select_tema_economia", options=[
            "Inflação", "Taxa de juros (Selic)", "Dívida pública", "Impostos e tributos",
            "Gastos públicos", "Orçamento público (PLOA)", "PIB", "Câmbio (dólar)",
            "Reforma tributária", "Teto de gastos", "Outro (perguntar)",
        ])
        pergunta_economia = ""
        if tema_economia == "Outro (perguntar)":
            pergunta_economia = st.text_input("O que você quer entender?", placeholder="ex: O que é superávit primário?", key="input_pergunta_economia")

        if st.button("💰 EXPLICAR ESSE TEMA"):
            topico = pergunta_economia if tema_economia == "Outro (perguntar)" and pergunta_economia.strip() else tema_economia
            if topico.strip():
                with st.spinner("Preparando explicação..."):
                    prompt = (
                        f"Explique de forma simples e didática o conceito econômico: {topico}\n\n"
                        f"FORMATO:\n\n"
                        f"💰 {topico.upper()}\n\n"
                        f"📖 O QUE É (em linguagem simples):\n[explicação clara, com analogia do dia a dia se possível]\n\n"
                        f"🔍 COMO ISSO AFETA SEU BOLSO:\n[impacto prático na vida das pessoas]\n\n"
                        f"📊 COMO É MEDIDO/DECIDIDO:\n[quem calcula ou decide isso, brevemente]\n\n"
                        f"⚖️ DIFERENTES VISÕES SOBRE O TEMA:\n[se houver debate econômico legítimo sobre esse tema, apresente as principais correntes de pensamento de forma equilibrada]\n\n"
                        f"❓ PERGUNTA FREQUENTE SOBRE O TEMA:\n[1 pergunta comum + resposta]"
                    )
                    res = cidada_ia(prompt)
                    salvar_consulta("Economia", topico, res)
                    st.session_state['economia_temp'] = res
            else:
                st.warning("Escolha ou descreva o tema.")

        if st.session_state.get('economia_temp'):
            st.markdown(f"<div class='card'>{st.session_state['economia_temp']}</div>", unsafe_allow_html=True)
            st.markdown(DISCLAIMER_PADRAO, unsafe_allow_html=True)
            col_dl, col_sv = st.columns(2)
            with col_dl:
                st.download_button("📋 Baixar (.txt)", data=st.session_state['economia_temp'], file_name="economia.txt", mime="text/plain", use_container_width=True)
            with col_sv:
                if st.button("❤️ Salvar", key="sv_eco", use_container_width=True):
                    st.session_state.consultas_salvas.append({'modulo':'Economia','tema':topico if 'topico' in dir() else '','conteudo':st.session_state['economia_temp'],'data':datetime.now().strftime('%d/%m %H:%M')})
                    st.success("❤️ Salvo!")

    # ========================
    # COMO FUNCIONA O GOVERNO
    # ========================
    elif st.session_state.pagina == "Governo":
        st.header("🏛️ Como Funciona o Governo")
        st.markdown("Entenda os 3 poderes e o papel de cada cargo público.")

        tema_governo = st.selectbox("Escolha um tema:", key="select_tema_governo", options=[
            "Poder Executivo", "Poder Legislativo", "Poder Judiciário",
            "O que faz um Presidente", "O que faz um Governador", "O que faz um Prefeito",
            "O que faz um Senador", "O que faz um Deputado Federal", "O que faz um Deputado Estadual",
            "O que faz um Vereador", "Como uma lei é aprovada", "Outro (perguntar)",
        ])
        pergunta_governo = ""
        if tema_governo == "Outro (perguntar)":
            pergunta_governo = st.text_input("O que você quer entender?", placeholder="ex: O que é uma medida provisória?", key="input_pergunta_governo")

        if st.button("🏛️ EXPLICAR ESSE TEMA"):
            topico = pergunta_governo if tema_governo == "Outro (perguntar)" and pergunta_governo.strip() else tema_governo
            if topico.strip():
                with st.spinner("Preparando explicação..."):
                    prompt = (
                        f"Explique de forma clara e didática: {topico}\n\n"
                        f"FORMATO:\n\n"
                        f"🏛️ {topico.upper()}\n\n"
                        f"📖 O QUE É / O QUE FAZ:\n[explicação institucional clara, factual]\n\n"
                        f"⚖️ PODERES E LIMITES:\n[o que esse poder/cargo pode e não pode fazer]\n\n"
                        f"🔄 COMO SE RELACIONA COM OS OUTROS PODERES/CARGOS:\n[sistema de freios e contrapesos quando aplicável]\n\n"
                        f"📅 MANDATO E ELEIÇÃO (se aplicável):\n[duração, como é eleito]\n\n"
                        f"❓ CURIOSIDADE OU DÚVIDA COMUM:\n[1 ponto que as pessoas costumam confundir sobre esse tema]"
                    )
                    res = cidada_ia(prompt)
                    salvar_consulta("Governo", topico, res)
                    st.session_state['governo_temp'] = res
            else:
                st.warning("Escolha ou descreva o tema.")

        if st.session_state.get('governo_temp'):
            st.markdown(f"<div class='card-blue'>{st.session_state['governo_temp']}</div>", unsafe_allow_html=True)
            st.markdown(DISCLAIMER_PADRAO, unsafe_allow_html=True)
            col_dl, col_sv = st.columns(2)
            with col_dl:
                st.download_button("📋 Baixar (.txt)", data=st.session_state['governo_temp'], file_name="governo.txt", mime="text/plain", use_container_width=True)
            with col_sv:
                if st.button("❤️ Salvar", key="sv_gov", use_container_width=True):
                    st.session_state.consultas_salvas.append({'modulo':'Governo','tema':topico if 'topico' in dir() else '','conteudo':st.session_state['governo_temp'],'data':datetime.now().strftime('%d/%m %H:%M')})
                    st.success("❤️ Salvo!")

    # ========================
    # TRADUTOR DE LEIS
    # ========================
    elif st.session_state.pagina == "Leis":
        st.header("📜 Tradutor de Leis")
        st.markdown("Cole um trecho de lei e receba a tradução em português simples.")

        texto_lei = st.text_area("📜 Cole o texto da lei ou trecho legal:", height=180,
            placeholder="Cole aqui o artigo de lei, trecho de contrato legal, ou texto jurídico que você quer entender...")

        if st.button("📜 TRADUZIR PARA LINGUAGEM SIMPLES"):
            if texto_lei.strip():
                with st.spinner("Traduzindo..."):
                    prompt = (
                        f"Traduza este texto legal para português simples, mantendo o sentido exato.\n\n"
                        f"Texto: {texto_lei}\n\n"
                        f"FORMATO:\n\n"
                        f"📜 TEXTO ORIGINAL (resumo):\n[1 linha identificando de que lei/artigo parece se tratar, se for possível inferir]\n\n"
                        f"💬 EM PORTUGUÊS SIMPLES:\n[a tradução clara, frase por frase se necessário, sem jargão jurídico]\n\n"
                        f"🎯 O QUE ISSO SIGNIFICA NA PRÁTICA:\n[impacto prático para uma pessoa comum]\n\n"
                        f"⚠️ TERMOS TÉCNICOS EXPLICADOS:\n[se houver termos jurídicos específicos no texto, explique cada um brevemente]"
                    )
                    res = cidada_ia(prompt)
                    salvar_consulta("Leis", texto_lei[:60], res)
                    st.session_state['lei_temp'] = res
            else:
                st.warning("Cole o texto da lei.")

        if st.session_state.get('lei_temp'):
            st.markdown(f"<div class='card-purple'>{st.session_state['lei_temp']}</div>", unsafe_allow_html=True)
            st.markdown("""<div class="disclaimer">⚠️ Esta tradução é educativa e pode simplificar nuances jurídicas importantes —
            para decisões legais reais, consulte um advogado ou o Consultor Jurídico do ecossistema.</div>""", unsafe_allow_html=True)
            col_dl, col_sv = st.columns(2)
            with col_dl:
                st.download_button("📋 Baixar (.txt)", data=st.session_state['lei_temp'], file_name="lei_traduzida.txt", mime="text/plain", use_container_width=True)
            with col_sv:
                if st.button("❤️ Salvar", key="sv_lei", use_container_width=True):
                    st.session_state.consultas_salvas.append({'modulo':'Leis','tema':texto_lei[:60] if 'texto_lei' in dir() else '','conteudo':st.session_state['lei_temp'],'data':datetime.now().strftime('%d/%m %H:%M')})
                    st.success("❤️ Salvo!")

    # ========================
    # APRENDA POLÍTICA
    # ========================
    elif st.session_state.pagina == "Aprenda":
        st.header("🎓 Aprenda Política")
        st.markdown("Pequenas aulas sobre conceitos políticos fundamentais.")

        conceito = st.selectbox("Escolha um conceito:", [
            "Democracia", "Federalismo", "Orçamento público", "Teto de gastos",
            "Reforma tributária", "Reforma administrativa", "Separação dos poderes",
            "Sistema proporcional (eleições)", "Sistema majoritário (eleições)",
            "Coligação partidária", "Plebiscito e referendo", "Outro (perguntar)",
        ])
        pergunta_conceito = ""
        if conceito == "Outro (perguntar)":
            pergunta_conceito = st.text_input("Qual conceito você quer aprender?", placeholder="ex: O que é parlamentarismo?")

        if st.button("🎓 GERAR AULA SOBRE ESSE TEMA"):
            topico = pergunta_conceito if conceito == "Outro (perguntar)" and pergunta_conceito.strip() else conceito
            if topico.strip():
                with st.spinner("Preparando a aula..."):
                    prompt = (
                        f"Crie uma pequena aula didática sobre: {topico}\n\n"
                        f"FORMATO:\n\n"
                        f"🎓 AULA: {topico.upper()}\n\n"
                        f"📖 DEFINIÇÃO SIMPLES:\n[explicação em 2-3 linhas, sem jargão]\n\n"
                        f"🌍 EXEMPLO PRÁTICO:\n[exemplo real ou hipotético que ilustre o conceito]\n\n"
                        f"🇧🇷 COMO ISSO SE APLICA NO BRASIL:\n[contexto institucional brasileiro, factual]\n\n"
                        f"⚖️ DIFERENTES VISÕES SOBRE O TEMA (se houver debate legítimo):\n[principais argumentos de diferentes correntes, sem indicar qual é certa]\n\n"
                        f"✅ RESUMO EM 1 FRASE:\n[a essência do conceito]"
                    )
                    res = cidada_ia(prompt)
                    salvar_consulta("Aprenda", topico, res)
                    st.session_state['aprenda_temp'] = res
            else:
                st.warning("Escolha ou descreva o conceito.")

        if st.session_state.get('aprenda_temp'):
            st.markdown(f"<div class='card-orange'>{st.session_state['aprenda_temp']}</div>", unsafe_allow_html=True)
            st.markdown(DISCLAIMER_PADRAO, unsafe_allow_html=True)
            col_dl, col_sv = st.columns(2)
            with col_dl:
                st.download_button("📋 Baixar (.txt)", data=st.session_state['aprenda_temp'], file_name="aula_politica.txt", mime="text/plain", use_container_width=True)
            with col_sv:
                if st.button("❤️ Salvar", key="sv_aprenda", use_container_width=True):
                    st.session_state.consultas_salvas.append({'modulo':'Aprenda','tema':topico if 'topico' in dir() else '','conteudo':st.session_state['aprenda_temp'],'data':datetime.now().strftime('%d/%m %H:%M')})
                    st.success("❤️ Salvo!")

    # ========================
    # PENSAMENTO CRÍTICO
    # ========================
    elif st.session_state.pagina == "Critico":
        st.header("🧠 Pensamento Crítico")
        st.markdown("Identifique vieses, falácias e manipulação emocional em qualquer texto — política, notícias ou redes sociais.")

        tab1, tab2 = st.tabs(["📝 Analisar um Texto", "📖 Aprender os Conceitos"])

        with tab1:
            texto_analise = st.text_area("📝 Cole o texto, discurso ou postagem que você quer analisar:", height=180,
                placeholder="Cole aqui qualquer texto — discurso, notícia, post de rede social...")

            if st.button("🧠 ANALISAR ESTE TEXTO"):
                if texto_analise.strip():
                    with st.spinner("Analisando..."):
                        prompt = (
                            f"Analise este texto com profundidade jornalística — identificando estrutura argumentativa, "
                            f"especificidade e técnicas retóricas — SEM julgar se o conteúdo é verdadeiro ou falso, bom ou ruim.\n\n"
                            f"Texto: {texto_analise}\n\n"
                            f"RESPONDA SEGUINDO EXATAMENTE ESTA ESTRUTURA, COM ESTES MARCADORES EXATOS (importante para o app renderizar corretamente):\n\n"
                            f"###TABELA_AFIRMACOES###\n"
                            f"[Para cada afirmação relevante do texto, uma linha no formato: Afirmação curta (até 8 palavras) | Tipo\n"
                            f"Tipo deve ser um de: Promessa / Objetivo político / Meta condicionada / Princípio administrativo / Opinião / Fato verificável / Depende de terceiros\n"
                            f"Liste de 3 a 7 afirmações. Uma por linha, separadas por |]\n\n"
                            f"###GRAU_OBJETIVIDADE###\n"
                            f"muito_especifico: [número de 1 a 5]\n"
                            f"moderadamente_especifico: [número de 1 a 5]\n"
                            f"generico: [número de 1 a 5]\n"
                            f"justificativa: [2-3 linhas explicando objetivamente o que falta no texto: valores, prazos, metas mensuráveis, fontes de recurso, indicadores — cite só o que realmente falta nesse texto]\n\n"
                            f"###TECNICAS_PERSUASAO###\n"
                            f"[Liste de 3 a 6 técnicas encontradas, uma por linha, cada uma começando com 'SIM:' ou 'NAO:' seguido do nome da técnica.\n"
                            f"Use apenas estas técnicas possíveis: Apelo à esperança, Apelo ao medo, Linguagem positiva, Promessa ampla, Poucos detalhes técnicos, "
                            f"Verbos de ação, Apelo à autoridade, Generalização, Ataque pessoal, Dados e números concretos, Comparação com outros lugares]\n\n"
                            f"###FALTA_PARA_AVALIAR###\n"
                            f"[Liste de 4 a 6 perguntas-padrão que ajudam a avaliar este TIPO de texto, uma por linha, simples, tipo 'Quanto custará?', 'Em quanto tempo?']\n\n"
                            f"###BENEFICIOS_POTENCIAIS###\n"
                            f"[Se as propostas/afirmações do texto fossem implementadas com sucesso, liste de 3 a 5 benefícios possíveis, um por linha, começando com ✔]\n\n"
                            f"###DESAFIOS_POTENCIAIS###\n"
                            f"[Liste de 3 a 5 desafios genéricos que esse TIPO de proposta/afirmação costuma enfrentar, um por linha, começando com •]\n\n"
                            f"###VERIFICABILIDADE###\n"
                            f"pode_ser_medido: [percentual 0-100 — o quanto as afirmações do texto permitem medição objetiva]\n"
                            f"tem_metas: [percentual 0-100 — o quanto há metas claras]\n"
                            f"tem_prazo: [percentual 0-100 — o quanto há prazos definidos]\n"
                            f"tem_numeros: [percentual 0-100 — o quanto há números/valores concretos]\n\n"
                            f"###VIES_EMOCIONAL###\n"
                            f"[Liste as emoções que o texto tenta despertar, uma por linha, no formato 'NOME_EMOCAO: intensidade' onde intensidade é Alta/Média/Baixa.\n"
                            f"Use emoções como: Esperança, Confiança, Otimismo, Medo, Indignação, Urgência, Orgulho, Pertencimento.\n"
                            f"Se não houver apelo ao medo ou conflito, declare isso explicitamente em uma linha separada começando com NOTA:]\n\n"
                            f"###PERGUNTAS_JORNALISTICAS###\n"
                            f"[Crie de 4 a 6 perguntas ESPECÍFICAS para este texto (não genéricas) no estilo jornalístico investigativo — "
                            f"sobre financiamento, percentual de orçamento, evidências de funcionamento em outros lugares, como medir sucesso, etc.\n"
                            f"Uma por linha, começando com um verbo de pergunta]\n\n"
                            f"###CONCEITOS_CITADOS###\n"
                            f"[Identifique de 3 a 6 conceitos técnicos mencionados ou implícitos no texto que merecem explicação "
                            f"(ex: infraestrutura, equilíbrio fiscal, geração de empregos, transparência, orçamento público, déficit, superávit).\n"
                            f"Para cada um, uma linha no formato: Conceito | explicação rápida de 1 frase]\n\n"
                            f"###NOTAS_FINAIS###\n"
                            f"clareza: [nota de 0 a 10 — o quão claro e compreensível é o texto, independente de ser específico]\n"
                            f"especificidade: [nota de 0 a 10 — o quanto o texto traz detalhes concretos vs generalidades]\n"
                            f"detalhamento: [nota de 0 a 10 — o nível de profundidade técnica fornecida]\n"
                            f"verificabilidade: [nota de 0 a 10 — o quanto seria possível checar/medir o que foi dito]\n"
                            f"viabilidade: [escreva 'Indeterminado (faltam informações)' SE não houver dados suficientes no texto para avaliar viabilidade prática; "
                            f"caso contrário escreva uma avaliação curta neutra]\n\n"
                            f"REGRAS CRÍTICAS:\n"
                            f"- Siga EXATAMENTE os marcadores ###NOME### — o app depende deles para renderizar\n"
                            f"- Nunca julgue se o conteúdo é verdadeiro, mentiroso, bom ou ruim — apenas estrutura, especificidade e técnica\n"
                            f"- Seja específico ao texto analisado, não genérico"
                        )
                        res = cidada_ia(prompt, "Trate isso como um exercício de literacia midiática e análise jornalística estrutural. Nunca classifique o conteúdo como verdadeiro/falso ou certo/errado — apenas identifique estrutura, especificidade e técnica argumentativa. Siga o formato de marcadores solicitado com precisão.")
                        salvar_consulta("Critico", texto_analise[:60], res)
                        st.session_state['critico_temp'] = res
                else:
                    st.warning("Cole o texto para analisar.")

            if st.session_state.get('critico_temp'):
                renderizar_analise_critica(st.session_state['critico_temp'])
                st.markdown(DISCLAIMER_PADRAO, unsafe_allow_html=True)
                col_dl, col_sv = st.columns(2)
                with col_dl:
                    st.download_button("📋 Baixar análise completa (.txt)", data=st.session_state['critico_temp'], file_name="analise_critica.txt", mime="text/plain", use_container_width=True)
                with col_sv:
                    if st.button("❤️ Salvar", key="sv_critico", use_container_width=True):
                        st.session_state.consultas_salvas.append({'modulo':'Critico','tema':texto_analise[:60] if 'texto_analise' in dir() else '','conteudo':st.session_state['critico_temp'],'data':datetime.now().strftime('%d/%m %H:%M')})
                        st.success("❤️ Salvo!")

        with tab2:
            conceito_critico = st.selectbox("Escolha um conceito para entender:", [
                "Viés de confirmação", "Falsa dicotomia", "Generalização apressada",
                "Apelo emocional", "Apelo à autoridade", "Ataque pessoal (ad hominem)",
                "Espantalho (distorcer o argumento do outro)", "Bandwagon (efeito manada)",
                "Linguagem persuasiva e eufemismos",
            ], key="select_conceito_critico")
            if st.button("📖 EXPLICAR ESSE CONCEITO"):
                with st.spinner("Preparando explicação..."):
                    prompt = (
                        f"Explique o conceito de pensamento crítico: {conceito_critico}\n\n"
                        f"FORMATO:\n\n"
                        f"🧠 {conceito_critico.upper()}\n\n"
                        f"📖 O QUE É:\n[definição clara e simples]\n\n"
                        f"💬 EXEMPLO GENÉRICO (sem citar pessoas ou casos reais específicos):\n[exemplo hipotético e neutro que ilustre o conceito — pode ser de qualquer área, não só política]\n\n"
                        f"🔍 COMO IDENTIFICAR:\n[sinais práticos para reconhecer isso em textos/discursos do dia a dia]\n\n"
                        f"🛡️ COMO SE PROTEGER:\n[1-2 dicas de como avaliar criticamente quando perceber isso]"
                    )
                    res = cidada_ia(prompt)
                    salvar_consulta("Critico", conceito_critico, res)
                    st.session_state['conceito_critico_temp'] = res

            if st.session_state.get('conceito_critico_temp'):
                st.markdown(f"<div class='card'>{st.session_state['conceito_critico_temp']}</div>", unsafe_allow_html=True)
                st.download_button("📋 Baixar (.txt)", data=st.session_state['conceito_critico_temp'], file_name="conceito_critico.txt", mime="text/plain", key="dl_conceito_critico")

    # ========================
    # ANTES DE VOTAR — CHECKLIST
    # ========================
    elif st.session_state.pagina == "Checklist":
        st.header("✅ Antes de Votar")
        st.markdown("Um checklist para organizar sua pesquisa antes de decidir seu voto — o conteúdo da pesquisa é só seu.")

        itens = [
            ("propostas", "📋 Pesquisei as propostas dos candidatos/partidos que considero"),
            ("experiencia", "📜 Pesquisei a experiência e histórico de atuação deles"),
            ("competencias", "🏛️ Entendo o que o cargo realmente pode fazer (competências e limites)"),
            ("viabilidade", "💰 Considerei a viabilidade prática das propostas (orçamento, apoio político)"),
            ("fontes", "🔍 Busquei informações em mais de uma fonte, incluindo fontes diferentes entre si"),
            ("local", "📍 Pesquisei também os cargos locais (vereador, prefeito), não só os mais divulgados"),
        ]

        marcados = 0
        for chave, label in itens:
            valor_atual = st.session_state.checklist_voto.get(chave, False)
            novo_valor = st.checkbox(label, value=valor_atual, key=f"check_voto_{chave}")
            st.session_state.checklist_voto[chave] = novo_valor
            if novo_valor:
                marcados += 1

        pct = round(marcados / len(itens) * 100)
        st.markdown("<br>", unsafe_allow_html=True)
        cor = "#22C55E" if pct == 100 else ("#F59E0B" if pct >= 50 else "#EF4444")
        st.markdown(f"""
        <div class="card" style="text-align:center;">
            <div style="font-size:0.85em;color:#555;">SEU PREPARO PARA VOTAR</div>
            <div style="font-size:2em;font-weight:700;color:{cor};font-family:'Playfair Display',serif;">{pct}%</div>
        </div>
        """, unsafe_allow_html=True)

        if pct == 100:
            st.success("✅ Você passou por todos os pontos do checklist. A decisão final é sua!")
        else:
            st.info(f"Faltam {len(itens) - marcados} item(ns). Use os outros módulos do app para te ajudar a completar.")

        st.markdown("""<div class="disclaimer">
        💡 Este checklist organiza o PROCESSO da sua pesquisa — o conteúdo das suas conclusões e sua decisão de voto
        são inteiramente pessoais e não são compartilhados com ninguém.
        </div>""", unsafe_allow_html=True)

    # ========================
    # BIBLIOTECA
    # ========================
    elif st.session_state.pagina == "Biblioteca":
        st.header("📚 Biblioteca de Consultas")

        if not st.session_state.consultas_salvas:
            st.info("Biblioteca vazia. Gere consultas nos módulos e salve as importantes aqui!")
        else:
            modulos_bib = list(set(c['modulo'] for c in st.session_state.consultas_salvas))
            filtro = st.selectbox("Filtrar por módulo:", ["Todos"] + modulos_bib, key="select_filtro_bib")
            consultas_f = [c for c in st.session_state.consultas_salvas if filtro == "Todos" or c['modulo'] == filtro]

            st.markdown(f"**{len(consultas_f)} consulta(s) encontrada(s)**")
            for i, item in enumerate(reversed(consultas_f)):
                idx_real = len(st.session_state.consultas_salvas) - 1 - i
                with st.expander(f"[{item['modulo']}] {item['tema'][:60]} — {item['data']}"):
                    st.markdown(f"<div class='card'>{item['conteudo']}</div>", unsafe_allow_html=True)
                    col_dl, col_del = st.columns([3, 1])
                    with col_dl:
                        st.download_button("📋 Baixar", data=item['conteudo'], file_name=f"{item['modulo'].lower()}.txt", mime="text/plain", key=f"dl_bib_{i}")
                    with col_del:
                        if st.button("🗑️ Remover", key=f"del_bib_{i}"):
                            st.session_state.consultas_salvas.pop(idx_real)
                            st.rerun()

        if st.session_state.historico_consultas:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            historico_txt = "\n\n".join(f"[{c['data']}] {c['modulo']} — {c['tema']}\n{c['conteudo']}\n{'─'*40}" for c in st.session_state.historico_consultas)
            st.download_button("⬇️ Exportar todo o histórico (.txt)", data=historico_txt, file_name="historico_cidada.txt", mime="text/plain")
            if st.button("🗑️ Limpar Todo o Histórico"):
                st.session_state.historico_consultas = []
                st.rerun()

# --- RODAPÉ ---
st.markdown(
    "<div style='text-align:center;color:#999;font-size:0.8em;margin-top:60px;'>"
    "© 2026 Decisão Cidadã — Consultor de Educação Cívica com IA · Quiz Com Prêmios"
    "</div>", unsafe_allow_html=True
)
