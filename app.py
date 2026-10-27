import streamlit as st
import pandas as pd
import sqlalchemy
from datetime import datetime, time, timedelta, date
import base64

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Stúdio de Pilates e Fisioterapia Ítalo e Letícia Sampaio",
    page_icon="🧘‍♀️",
    layout="wide"
)

# ==============================================================================
# ESTILIZAÇÃO CSS CUSTOMIZADA
# ==============================================================================
st.markdown("""
    <style>
    .stApp {
        background-color: #f8faf9;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    .header-container {
        background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 50%, #40916c 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: white;
        box-shadow: 0 8px 20px rgba(27, 67, 50, 0.15);
        margin-bottom: 25px;
        text-align: center;
    }
    .main-title {
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .sub-title {
        font-size: 1.05rem !important;
        color: #d8f3dc !important;
        margin-top: 6px !important;
        font-weight: 400;
    }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
        border-left: 5px solid #2d6a4f;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #52b788 !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        color: #1b4332 !important;
        font-weight: 700 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        background-color: #e8f5e9;
        color: #2d6a4f;
        font-weight: 600;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2d6a4f !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS (SUPABASE)
# ==============================================================================
def conectar_bd():
    # URL de conexão direta e estável com o Supabase
    db_url = "postgresql+psycopg2://postgres:cD9QEGjsV01MkqI6@db.didwkuzlfbdudqrlvkpu.supabase.co:5432/postgres"
    engine = sqlalchemy.create_engine(db_url)
    return engine

engine = conectar_bd()

def inicializar_tabelas():
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text('''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                cpf TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                email TEXT,
                data_nascimento TEXT,
                idade INTEGER,
                endereco TEXT,
                telefone TEXT,
                contato_emergencia TEXT,
                objetivo TEXT,
                plano TEXT,
                dias_semana TEXT,
                horarios TEXT
            )
        '''))
        conn.execute(sqlalchemy.text('''
            CREATE TABLE IF NOT EXISTS profissionais (
                id SERIAL PRIMARY KEY,
                nome_prof TEXT NOT NULL,
                conselho TEXT NOT NULL,
                registro TEXT NOT NULL
            )
        '''))
        conn.execute(sqlalchemy.text('''
            CREATE TABLE IF NOT EXISTS prontuarios (
                id SERIAL PRIMARY KEY,
                cpf_cliente TEXT NOT NULL,
                data_atendimento TEXT NOT NULL,
                profissional TEXT NOT NULL,
                atividades TEXT NOT NULL,
                evolucao TEXT NOT NULL
            )
        '''))
        conn.execute(sqlalchemy.text('''
            CREATE TABLE IF NOT EXISTS documentos_pacientes (
                id SERIAL PRIMARY KEY,
                cpf_cliente TEXT NOT NULL,
                nome_arquivo TEXT NOT NULL,
                tipo_documento TEXT NOT NULL,
                arquivo_bytes BYTEA,
                data_upload TEXT NOT NULL
            )
        '''))

inicializar_tabelas()

def adicionar_cliente(cpf, nome, email, data_nasc, idade, endereco, telefone, contato_emergencia, objetivo, plano, dias_semana, horarios, arquivo_upload=None, tipo_doc=""):
    dias_str = ", ".join(dias_semana)
    horarios_str = ", ".join(horarios)
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text('''
                INSERT INTO clientes (cpf, nome, email, data_nascimento, idade, endereco, telefone, contato_emergencia, objetivo, plano, dias_semana, horarios)
                VALUES (:cpf, :nome, :email, :data_nascimento, :idade, :endereco, :telefone, :contato_emergencia, :objetivo, :plano, :dias_semana, :horarios)
            '''), {
                "cpf": cpf, "nome": nome, "email": email, "data_nascimento": data_nasc,
                "idade": idade, "endereco": endereco, "telefone": telefone, "contato_emergencia": contato_emergencia,
                "objetivo": objetivo, "plano": plano, "dias_semana": dias_str, "horarios": horarios_str
            })

            if arquivo_upload is not None:
                bytes_dados = arquivo_upload.getvalue()
                data_hoje = datetime.today().strftime("%d/%m/%Y")
                
                conn.execute(sqlalchemy.text('''
                    INSERT INTO documentos_pacientes (cpf_cliente, nome_arquivo, tipo_documento, arquivo_bytes, data_upload)
                    VALUES (:cpf, :nome_arq, :tipo, :bytes, :data_up)
                '''), {
                    "cpf": cpf, "nome_arq": arquivo_upload.name, "tipo": tipo_doc,
                    "bytes": bytes_dados, "data_up": data_hoje
                })

                conn.execute(sqlalchemy.text('''
                    INSERT INTO prontuarios (cpf_cliente, data_atendimento, profissional, atividades, evolucao)
                    VALUES (:cpf, :data, :prof, :atividades, :evolucao)
                '''), {
                    "cpf": cpf,
                    "data": data_hoje,
                    "prof": "SECRETARIA / RECEPÇÃO (TRIAGEM)",
                    "atividades": f"APRESENTAÇÃO DE {tipo_doc.upper()} ({arquivo_upload.name})",
                    "evolucao": f"⚠️ ATENÇÃO FISIOTERAPEUTA: O paciente apresentou {tipo_doc.lower()} no momento do cadastro. Documento digitalizado/anexado para conduta clínica direcionada."
                })

        return True, "Cliente cadastrado com sucesso!"
    except Exception as e:
        return False, f"Erro: CPF já cadastrado ou falha na operação."

def adicionar_documento_extra(cpf, arquivo_upload, tipo_doc):
    try:
        with engine.begin() as conn:
            bytes_dados = arquivo_upload.getvalue()
            data_hoje = datetime.today().strftime("%d/%m/%Y")
            
            conn.execute(sqlalchemy.text('''
                INSERT INTO documentos_pacientes (cpf_cliente, nome_arquivo, tipo_documento, arquivo_bytes, data_upload)
                VALUES (:cpf, :nome_arq, :tipo, :bytes, :data_up)
            '''), {
                "cpf": cpf, "nome_arq": arquivo_upload.name, "tipo": tipo_doc,
                "bytes": bytes_dados, "data_up": data_hoje
            })

            conn.execute(sqlalchemy.text('''
                INSERT INTO prontuarios (cpf_cliente, data_atendimento, profissional, atividades, evolucao)
                VALUES (:cpf, :data, :prof, :atividades, :evolucao)
            '''), {
                "cpf": cpf,
                "data": data_hoje,
                "prof": "SECRETARIA / RECEPÇÃO (ATUALIZAÇÃO)",
                "atividades": f"NOVO {tipo_doc.upper()} ADICIONADO ({arquivo_upload.name})",
                "evolucao": f"📌 Atualização cadastral: Novo(a) {tipo_doc.lower()} anexado(a) pela recepção para consulta da equipe clínica."
            })
        return True, "Documento adicionado com sucesso!"
    except Exception as e:
        return False, f"Erro ao anexar documento: {e}"

def carregar_clientes():
    return pd.read_sql("SELECT * FROM clientes", engine)

def carregar_documentos(cpf):
    return pd.read_sql(sqlalchemy.text("SELECT * FROM documentos_pacientes WHERE cpf_cliente = :cpf"), engine, params={"cpf": cpf})

def adicionar_profissional(nome, conselho, registro):
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text('''
            INSERT INTO profissionais (nome_prof, conselho, registro)
            VALUES (:nome, :conselho, :registro)
        '''), {"nome": nome, "conselho": conselho, "registro": registro})

def carregar_profissionais():
    return pd.read_sql("SELECT * FROM profissionais", engine)

def adicionar_prontuario(cpf, data, profissional, atividades, evolucao):
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text('''
            INSERT INTO prontuarios (cpf_cliente, data_atendimento, profissional, atividades, evolucao)
            VALUES (:cpf, :data, :profissional, :atividades, :evolucao)
        '''), {"cpf": cpf, "data": data, "profissional": profissional, "atividades": atividades, "evolucao": evolucao})

def carregar_prontuarios(cpf=""):
    if cpf:
        return pd.read_sql(sqlalchemy.text("SELECT * FROM prontuarios WHERE cpf_cliente = :cpf ORDER BY id DESC"), engine, params={"cpf": cpf})
    return pd.read_sql("SELECT * FROM prontuarios ORDER BY id DESC", engine)

# ==============================================================================
# FORMATAÇÃO
# ==============================================================================
def formatar_cpf(texto):
    nums = "".join(filter(str.isdigit, texto))[:11]
    if len(nums) == 11:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"
    return texto.upper()

def formatar_telefone(texto):
    nums = "".join(filter(str.isdigit, texto))[:11]
    if len(nums) == 11:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    elif len(nums) == 10:
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return texto.upper()

def formatar_data(texto):
    nums = "".join(filter(str.isdigit, texto))[:8]
    if len(nums) == 8:
        return f"{nums[:2]}/{nums[2:4]}/{nums[4:]}"
    return texto.upper()

# ==============================================================================
# INTERFACE PRINCIPAL
# ==============================================================================
st.markdown("""
    <div class="header-container">
        <h1 class="main-title">🧘‍♀️ Clínica de Fisioterapia e Pilates Letícia e Ítalo Sampaio</h1>
        <p class="sub-title">Painel de Gestão Integrada: Financeiro, Agenda Visual, Clientes e Prontuários</p>
    </div>
""", unsafe_allow_html=True)

aba_financeiro, aba_clientes, aba_mapa, aba_profissionais, aba_prontuario = st.tabs([
    "📊 Painel Financeiro", 
    "👥 Agendamento & Clientes", 
    "🧩 Mapa de Ocupação",
    "👩‍⚕️ Profissionais", 
    "📝 Prontuário Eletrônico"
])

# --- ABA 1: FINANCEIRO ---
with aba_financeiro:
    st.caption("Ajuste os parâmetros na barra lateral para simular faturamento e margens.")
    st.sidebar.header("⚙️ Parâmetros do Estúdio")
    vagas_por_turma = st.sidebar.number_input("Alunos/Vagas por Turma", min_value=1, max_value=10, value=2)
    horas_por_dia = st.sidebar.number_input("Horas de Aula por Dia", min_value=1, max_value=18, value=10)
    dias_por_semana = st.sidebar.number_input("Dias de Funcionamento/Semana", min_value=1, max_value=7, value=5)

    comissao_prof_hora = st.sidebar.number_input("Comissão do Professor (R$/hora)", min_value=0.0, value=45.0, step=5.0)
    custos_fixos = st.sidebar.number_input("Custos Fixos Mensais (R$)", min_value=0.0, value=8000.0, step=500.0)
    imposto_pct = st.sidebar.slider("Imposto / Simples Nacional (%)", min_value=0.0, max_value=20.0, value=6.0) / 100

    preco_1x = st.sidebar.number_input("Plano 1x por semana (R$)", value=250.0, step=10.0)
    preco_2x = st.sidebar.number_input("Plano 2x por semana (R$)", value=380.0, step=10.0)
    preco_3x = st.sidebar.number_input("Plano 3x por semana (R$)", value=480.0, step=10.0)
    preco_ilimitado = st.sidebar.number_input("Plano Ilimitado (R$)", value=650.0, step=10.0)

    aulas_semanais = horas_por_dia * dias_por_semana
    aulas_mensais = aulas_semanais * 4.33
    custo_professores_mes = aulas_mensais * comissao_prof_hora

    df_cadastrados_fin = carregar_clientes()
    if not df_cadastrados_fin.empty:
        contagem_planos = df_cadastrados_fin['plano'].value_counts()
        faturamento_real = (contagem_planos.get("Plano 1x por semana", 0) * preco_1x) + \
                           (contagem_planos.get("Plano 2x por semana", 0) * preco_2x) + \
                           (contagem_planos.get("Plano 3x por semana", 0) * preco_3x) + \
                           (contagem_planos.get("Plano Ilimitado", 0) * preco_ilimitado)
        impostos_reais = faturamento_real * imposto_pct
        lucro_real = faturamento_real - (custos_fixos + impostos_reais + custo_professores_mes)

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total de Alunos", f"{len(df_cadastrados_fin)} alunos")
        r2.metric("Faturamento Bruto Real", f"R$ {faturamento_real:,.2f}")
        r3.metric("Impostos Reais", f"R$ {impostos_reais:,.2f}")
        r4.metric("Lucro Líquido Real", f"R$ {lucro_real:,.2f}")
    else:
        st.info("Nenhum cliente cadastrado no momento.")

# --- HORÁRIOS E OCUPAÇÃO ---
horarios_base = []
inicio_manha = datetime.combine(datetime.today(), time(8, 0))
fim_manha = datetime.combine(datetime.today(), time(12, 0))
atual = inicio_manha
while atual + timedelta(minutes=45) <= fim_manha:
    horarios_base.append(atual.strftime("%H:%M"))
    atual += timedelta(minutes=60)
    
inicio_tarde = datetime.combine(datetime.today(), time(14, 0))
fim_tarde = datetime.combine(datetime.today(), time(21, 0))
atual = inicio_tarde
while atual + timedelta(minutes=45) <= fim_tarde:
    horarios_base.append(atual.strftime("%H:%M"))
    atual += timedelta(minutes=60)

dias_semana_lista = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"]

def calcular_ocupacao_matriz(df_clientes, limite_vagas):
    ocupacao = {(d, h): 0 for d in dias_semana_lista for h in horarios_base}
    if not df_clientes.empty:
        for _, row in df_clientes.iterrows():
            if pd.notna(row.get('dias_semana')) and pd.notna(row.get('horarios')):
                dias_cli = [x.strip() for x in row['dias_semana'].split(",") if x.strip()]
                hors_cli = [x.strip() for x in row['horarios'].split(",") if x.strip()]
                for d in dias_cli:
                    for h in hors_cli:
                        if (d, h) in ocupacao:
                            ocupacao[(d, h)] += 1
    return ocupacao

# --- ABA 2: CLIENTES & CADASTRO ---
with aba_clientes:
    sub_aba_novo, sub_aba_gerenciar = st.tabs(["➕ Novo Cadastro", "✏️ Gerenciar Anexos"])

    with sub_aba_novo:
        if "limpar_campos" not in st.session_state:
            st.session_state.limpar_campos = False

        if st.session_state.limpar_campos:
            st.session_state.input_cpf = ""
            st.session_state.input_nome = ""
            st.session_state.input_email = ""
            st.session_state.input_nasc_texto = ""
            st.session_state.input_end = ""
            st.session_state.input_tel = ""
            st.session_state.input_nome_emerg = ""
            st.session_state.input_tel_emerg = ""
            st.session_state.input_obj = ""
            st.session_state.input_dias = []
            st.session_state.limpar_campos = False

        df_atual_clientes = carregar_clientes()
        vagas_limite = vagas_por_turma
        ocupacao_matriz = calcular_ocupacao_matriz(df_atual_clientes, vagas_limite)

        col_form, col_lista = st.columns([1, 2])
        
        with col_form:
            st.subheader("Novo Cadastro & Agendamento")
            cpf = formatar_cpf(st.text_input("CPF (ID do Paciente)*", key="input_cpf"))
            nome = st.text_input("Nome Completo*", key="input_nome").upper()
            email = st.text_input("E-mail", key="input_email").lower()
            data_nasc = formatar_data(st.text_input("Data de Nascimento (DD/MM/AAAA)", key="input_nasc_texto"))
            
            idade_calculada = None
            if len(data_nasc) == 10:
                try:
                    dt = datetime.strptime(data_nasc, "%d/%m/%Y").date()
                    hoje = date.today()
                    idade_calculada = hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
                    st.info(f"🎂 Idade calculada: {idade_calculada} anos")
                except ValueError:
                    pass

            endereco = st.text_input("Endereço", key="input_end").upper()
            telefone = formatar_telefone(st.text_input("Telefone / WhatsApp", key="input_tel"))
            nome_emerg = st.text_input("Nome Contato de Emergência", key="input_nome_emerg").upper()
            tel_emerg = formatar_telefone(st.text_input("Telefone Contato de Emergência", key="input_tel_emerg"))
            contato_emergencia = f"{nome_emerg} — {tel_emerg}" if nome_emerg or tel_emerg else ""

            objetivo = st.text_area("Objetivo Clínico / Restrições", key="input_obj").upper()
            plano = st.selectbox("Plano Contratado", ["Plano 1x por semana", "Plano 2x por semana", "Plano 3x por semana", "Plano Ilimitado"], key="input_plano")
            
            st.markdown("---")
            tem_documento = st.checkbox("O paciente apresentou receita médica ou laudo no cadastro?")
            arquivo_enviado = None
            tipo_documento_escolhido = "Receita Médica"
            if tem_documento:
                tipo_documento_escolhido = st.selectbox("Tipo de Documento", ["Receita Médica", "Laudo Médico", "Exame de Imagem"])
                arquivo_enviado = st.file_uploader("Enviar Arquivo (PDF ou Imagem do Scanner/E-mail)", type=["pdf", "png", "jpg", "jpeg"])

            dias_escolhidos = st.multiselect("Selecione o(s) Dia(s) da Semana da Aula", dias_semana_lista, key="input_dias")
            horarios_por_dia_escolhido = []
            tem_algum_dia_sem_vaga = False
            
            if dias_escolhidos:
                for dia in dias_escolhidos:
                    opcoes_dia = []
                    mapa_rotulos = {}
                    for h in horarios_base:
                        ocupados_neste_dia = ocupacao_matriz.get((dia, h), 0)
                        vagas_restantes = vagas_limite - ocupados_neste_dia
                        if vagas_restantes > 0:
                            rotulo = f"⏰ {h} — [{vagas_restantes}/{vagas_limite} vagas livres 🟢]"
                            opcoes_dia.append(rotulo)
                            mapa_rotulos[rotulo] = h
                    if not opcoes_dia:
                        st.error(f"⚠️ Turmas do dia **{dia}** esgotadas!")
                        tem_algum_dia_sem_vaga = True
                    else:
                        escolha_rotulo = st.selectbox(f"Horário para **{dia}**:", opcoes_dia, key=f"horario_{dia}")
                        horarios_por_dia_escolhido.append(mapa_rotulos[escolha_rotulo])

            if st.button("💾 Salvar e Confirmar Agendamento", type="primary"):
                if not cpf.strip() or not nome.strip():
                    st.warning("Preencha o CPF e o Nome Completo.")
                elif not dias_escolhidos:
                    st.warning("Selecione pelo menos um dia da semana.")
                elif tem_algum_dia_sem_vaga:
                    st.error("⚠️ Há dias selecionados sem vagas.")
                else:
                    idade_final = idade_calculada if idade_calculada is not None else 0
                    sucesso, msg = adicionar_cliente(
                        cpf, nome, email, data_nasc, idade_final, endereco, telefone, 
                        contato_emergencia, objetivo, plano, dias_escolhidos, horarios_por_dia_escolhido,
                        arquivo_upload=arquivo_enviado, tipo_doc=tipo_documento_escolhido
                    )
                    if sucesso:
                        st.success(msg)
                        st.session_state.limpar_campos = True
                        st.rerun()
                    else:
                        st.error(msg)

        with col_lista:
            st.subheader("👥 Clientes Cadastrados")
            if not df_atual_clientes.empty:
                busca = st.text_input("🔍 Buscar cliente:", "", key="busca_cli")
                df_exibicao = df_atual_clientes.copy()
                if busca:
                    df_exibicao = df_exibicao[df_exibicao['nome'].str.contains(busca, case=False, na=False)]
                st.dataframe(df_exibicao, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum cliente cadastrado.")

    with sub_aba_gerenciar:
        st.subheader("✏️ Adicionar Laudos ou Receitas Extras")
        df_cli_gerir = carregar_clientes()
        if not df_cli_gerir.empty:
            lista_edit = [f"{r['nome']} (CPF: {r['cpf']})" for _, r in df_cli_gerir.iterrows()]
            escolha_cli = st.selectbox("Selecione o cliente:", lista_edit)
            cpf_selecionado = escolha_cli.split("CPF: ")[1].split(")")[0]
            
            with st.container(border=True):
                st.markdown("📎 **Novo Laudo, Receita ou Exame**")
                with st.form("form_doc_extra"):
                    tipo_extra = st.selectbox("Tipo", ["Receita Médica", "Laudo Médico", "Exame de Imagem"])
                    arq_extra = st.file_uploader("Arquivo (PDF/Imagem)", type=["pdf", "png", "jpg", "jpeg"])
                    if st.form_submit_button("📤 Enviar Documento"):
                        if arq_extra:
                            adicionar_documento_extra(cpf_selecionado, arq_extra, tipo_extra)
                            st.success("Documento adicionado e prontuário atualizado!")
                            st.rerun()
                        else:
                            st.warning("Selecione um arquivo.")

# --- ABA 3: MAPA DE OCUPAÇÃO ---
with aba_mapa:
    st.header("🧩 Mapa de Ocupação das Turmas")
    df_mapa = carregar_clientes()
    matriz = calcular_ocupacao_matriz(df_mapa, vagas_por_turma)
    for dia in dias_semana_lista:
        st.subheader(f"📅 {dia}")
        cols = st.columns(len(horarios_base))
        for idx, h in enumerate(horarios_base):
            qtd = matriz.get((dia, h), 0)
            livres = max(0, vagas_por_turma - qtd)
            with cols[idx]:
                st.markdown(f"**{h}**")
                st.markdown(("🧘‍♀️ " * qtd) + ("🟢 " * livres))
                st.caption(f"[{qtd}/{vagas_por_turma} vagas]")
        st.markdown("---")

# --- ABA 4: PROFISSIONAIS ---
with aba_profissionais:
    st.header("👩‍⚕️ Gestão de Fisioterapeutas")
    with st.form("f_prof", clear_on_submit=True):
        nome_p = st.text_input("Nome*").upper()
        conselho = st.selectbox("Conselho", ["CREFITO", "CREF", "Outro"])
        reg = st.text_input("Registro*").upper()
        if st.form_submit_button("Salvar Profissional"):
            if nome_p and reg:
                adicionar_profissional(nome_p, conselho, reg)
                st.success("Cadastrado com sucesso!")
                st.rerun()
    st.divider()
    df_p = carregar_profissionais()
    if not df_p.empty:
        st.dataframe(df_p, hide_index=True)

# --- ABA 5: PRONTUÁRIO ---
with aba_prontuario:
    st.header("📝 Prontuário Eletrônico")
    df_c = carregar_clientes()
    df_p = carregar_profissionais()
    
    if not df_c.empty and not df_p.empty:
        pacientes = [f"{r['nome']} (CPF: {r['cpf']})" for _, r in df_c.iterrows()]
        escolhido = st.selectbox("Selecione o Paciente", pacientes)
        cpf_atual = escolhido.split("CPF: ")[1].split(")")[0]
        dados_p = df_c[df_c['cpf'] == cpf_atual].iloc[0]
        
        with st.expander("📌 Ver Cadastro e Laudos Anexados", expanded=False):
            st.write(f"**Objetivo:** {dados_p.get('objetivo', '-')}")
            st.markdown("📂 **Documentos do Paciente:**")
            df_docs = carregar_documentos(cpf_atual)
            if not df_docs.empty:
                for _, doc in df_docs.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"• **{doc['tipo_documento']}:** {doc['nome_arquivo']} *({doc['data_upload']})*")
                    if doc['arquivo_bytes']:
                        b64 = base64.b64encode(doc['arquivo_bytes']).decode('utf-8')
                        c2.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="{doc["nome_arquivo"]}">📥 Baixar</a>', unsafe_allow_html=True)
            else:
                st.info("Nenhum documento anexado.")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("➕ Nova Evolução")
            with st.form("f_ev", clear_on_submit=True):
                data_at = st.date_input("Data do Atendimento", value=datetime.today())
                prof_resp = st.selectbox("Profissional Responsável", [f"{r['nome_prof']} ({r['conselho']}: {r['registro']})" for _, r in df_p.iterrows()])
                atividades = st.text_area("Atividades Realizadas").upper()
                evolucao = st.text_area("Evolução Clínica").upper()
                if st.form_submit_button("Salvar Prontuário"):
                    if atividades and evolucao:
                        adicionar_prontuario(cpf_atual, data_at.strftime("%d/%m/%Y"), prof_resp, atividades, evolucao)
                        st.success("Prontuário salvo com sucesso!")
                        st.rerun()
        with col2:
            st.subheader("📖 Histórico de Atendimentos")
            df_hist = carregar_prontuarios(cpf_atual)
            if not df_hist.empty:
                for _, h in df_hist.iterrows():
                    with st.container(border=True):
                        st.markdown(f"📅 **Data:** {h['data_atendimento']} | 👩‍⚕️ **Profissional:** {h['profissional']}")
                        st.markdown(f"🏋️ **Atividades:** {h['atividades']}")
                        st.markdown(f"📝 **Evolução:** {h['evolucao']}")
            else:
                st.info("Nenhum atendimento registrado.")