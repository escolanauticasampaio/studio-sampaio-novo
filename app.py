import streamlit as st
import pandas as pd
import sqlite3
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
# CONFIGURAÇÃO DO BANCO DE DADOS (SQLite)
# ==============================================================================
def conectar_bd():
    conn = sqlite3.connect("clientes_studio_v2.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    ''')
    
    cursor.execute("PRAGMA table_info(clientes)")
    colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
    for col, tipo in {"email": "TEXT", "data_nascimento": "TEXT", "contato_emergencia": "TEXT"}.items():
        if col not in colunas_existentes:
            cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profissionais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_prof TEXT NOT NULL,
            conselho TEXT NOT NULL,
            registro TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prontuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf_cliente TEXT NOT NULL,
            data_atendimento TEXT NOT NULL,
            profissional TEXT NOT NULL,
            atividades TEXT NOT NULL,
            evolucao TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receitas_laudos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf_cliente TEXT NOT NULL,
            data_recebimento TEXT NOT NULL,
            titulo TEXT NOT NULL,
            origem TEXT NOT NULL,
            descricao_conteudo TEXT,
            nome_arquivo TEXT,
            arquivo_bin BLOB
        )
    ''')
    
    conn.commit()
    return conn

conn = conectar_bd()

def adicionar_cliente(cpf, nome, email, data_nasc, idade, endereco, telefone, contato_emergencia, objetivo, plano, dias_semana, horarios):
    cursor = conn.cursor()
    dias_str = ", ".join(dias_semana)
    horarios_str = ", ".join(horarios)
    
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE cpf = ?", (cpf,))
    existe = cursor.fetchone()[0] > 0
    
    if existe:
        return False, "⚠️ Já existe um cliente cadastrado com este CPF!"
    
    try:
        cursor.execute('''
            INSERT INTO clientes (cpf, nome, email, data_nascimento, idade, endereco, telefone, contato_emergencia, objetivo, plano, dias_semana, horarios)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cpf, nome, email, data_nasc, idade, endereco, telefone, contato_emergencia, objetivo, plano, dias_str, horarios_str))
        conn.commit()
        return True, "🎉 Cadastro realizado com Sucesso!"
    except sqlite3.IntegrityError:
        return False, "Erro: Já existe um cliente cadastrado com este CPF!"

def atualizar_cliente(cpf_antigo, nome, email, data_nasc, idade, endereco, telefone, contato_emergencia, objetivo, plano, dias_semana, horarios):
    cursor = conn.cursor()
    dias_str = ", ".join(dias_semana)
    horarios_str = ", ".join(horarios)
    cursor.execute('''
        UPDATE clientes 
        SET nome = ?, email = ?, data_nascimento = ?, idade = ?, endereco = ?, telefone = ?, contato_emergencia = ?, objetivo = ?, plano = ?, dias_semana = ?, horarios = ?
        WHERE cpf = ?
    ''', (nome, email, data_nasc, idade, endereco, telefone, contato_emergencia, objetivo, plano, dias_str, horarios_str, cpf_antigo))
    conn.commit()
    return True, "Cliente atualizado com sucesso!"

def deletar_cliente(cpf):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE cpf = ?", (cpf,))
    cursor.execute("DELETE FROM receitas_laudos WHERE cpf_cliente = ?", (cpf,))
    cursor.execute("DELETE FROM prontuarios WHERE cpf_cliente = ?", (cpf,))
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='clientes'")
        conn.commit()

def limpa_todos_clientes():
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes")
    cursor.execute("DELETE FROM receitas_laudos")
    cursor.execute("DELETE FROM prontuarios")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='clientes'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='receitas_laudos'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='prontuarios'")
    conn.commit()

def carregar_clientes():
    return pd.read_sql_query("SELECT * FROM clientes", conn)

def adicionar_profissional(nome, conselho, registro):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO profissionais (nome_prof, conselho, registro)
        VALUES (?, ?, ?)
    ''', (nome, conselho, registro))
    conn.commit()

def atualizar_profissional(prof_id, nome, conselho, registro):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE profissionais 
        SET nome_prof = ?, conselho = ?, registro = ?
        WHERE id = ?
    ''', (nome, conselho, registro, prof_id))
    conn.commit()

def deletar_profissional(prof_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profissionais WHERE id = ?", (prof_id,))
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM profissionais")
    if cursor.fetchone()[0] == 0:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='profissionais'")
        conn.commit()

def carregar_profissionais():
    return pd.read_sql_query("SELECT * FROM profissionais", conn)

def adicionar_prontuario(cpf, data_hora, profissional, atividades, evolucao):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO prontuarios (cpf_cliente, data_atendimento, profissional, atividades, evolucao)
        VALUES (?, ?, ?, ?, ?)
    ''', (cpf, data_hora, profissional, atividades, evolucao))
    conn.commit()

def atualizar_prontuario(prontuario_id, atividades, evolucao):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE prontuarios 
        SET atividades = ?, evolucao = ?
        WHERE id = ?
    ''', (atividades, evolucao, prontuario_id))
    conn.commit()

def deletar_prontuario(prontuario_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prontuarios WHERE id = ?", (prontuario_id,))
    conn.commit()

def carregar_prontuarios(cpf=""):
    if cpf:
        return pd.read_sql_query("SELECT * FROM prontuarios WHERE cpf_cliente = ?", conn, params=(cpf,))
    return pd.read_sql_query("SELECT * FROM prontuarios", conn)

def adicionar_receita_laudo(cpf, data_hora, titulo, origem, descricao, nome_arq, bin_arq):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO receitas_laudos (cpf_cliente, data_recebimento, titulo, origem, descricao_conteudo, nome_arquivo, arquivo_bin)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (cpf, data_hora, titulo, origem, descricao, nome_arq, bin_arq))
    conn.commit()

def deletar_receita_laudo(doc_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM receitas_laudos WHERE id = ?", (doc_id,))
    conn.commit()

def carregar_receitas_laudos(cpf=""):
    if cpf:
        return pd.read_sql_query("SELECT * FROM receitas_laudos WHERE cpf_cliente = ?", conn, params=(cpf,))
    return pd.read_sql_query("SELECT * FROM receitas_laudos", conn)

# ==============================================================================
# FUNÇÕES DE FORMATAÇÃO PADRÃO
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
# CABEÇALHO PERSONALIZADO
# ==============================================================================
st.markdown("""
    <div class="header-container">
        <h1 class="main-title">🧘‍♀️ Clínica de Fisioterapia e Pilates Letícia e Ítalo Sampaio</h1>
        <p class="sub-title">Painel de Gestão Integrada: Financeiro, Agenda Visual, Clientes, Laudos e Prontuários</p>
    </div>
""", unsafe_allow_html=True)

aba_financeiro, aba_clientes, aba_mapa, aba_profissionais, aba_prontuario = st.tabs([
    "📊 Painel Financeiro", 
    "👥 Agendamento & Clientes", 
    "🧩 Mapa de Ocupação",
    "👩‍⚕️ Profissionais", 
    "📝 Prontuário & Laudos"
])

# ==============================================================================
# ABA 1: PAINEL FINANCEIRO
# ==============================================================================
with aba_financeiro:
    st.caption("Ajuste os parâmetros na barra lateral para simular faturamento, custos com professores e margens de lucro.")

    st.sidebar.header("⚙️ Parâmetros do Estúdio")
    st.sidebar.subheader("1. Estrutura e Capacidade")
    vagas_por_turma = st.sidebar.number_input("Alunos/Vagas por Turma", min_value=1, max_value=10, value=2, key="vagas_sidebar")
    horas_por_dia = st.sidebar.number_input("Horas de Aula por Dia", min_value=1, max_value=18, value=10)
    dias_por_semana = st.sidebar.number_input("Dias de Funcionamento/Semana", min_value=1, max_value=7, value=5)

    st.sidebar.subheader("2. Custos e Comissão de Professores")
    comissao_prof_hora = st.sidebar.number_input("Comissão do Professor (R$/hora)", min_value=0.0, value=45.0, step=5.0)
    custos_fixos = st.sidebar.number_input("Custos Fixos Mensais (R$)", min_value=0.0, value=8000.0, step=500.0)
    imposto_pct = st.sidebar.slider("Imposto / Simples Nacional (%)", min_value=0.0, max_value=20.0, value=6.0) / 100

    st.sidebar.subheader("3. Preços dos Planos (Mensalidade)")
    preco_1x = st.sidebar.number_input("Plano 1x por semana (R$)", value=250.0, step=10.0)
    preco_2x = st.sidebar.number_input("Plano 2x por semana (R$)", value=380.0, step=10.0)
    preco_3x = st.sidebar.number_input("Plano 3x por semana (R$)", value=480.0, step=10.0)
    preco_ilimitado = st.sidebar.number_input("Plano Ilimitado (R$)", value=650.0, step=10.0)

    aulas_semanais = horas_por_dia * dias_por_semana
    aulas_mensais = aulas_semanais * 4.33
    capacidade_slots_semanais = aulas_semanais * vagas_por_turma
    custo_professores_mes = aulas_mensais * comissao_prof_hora

    cenarios = [
        {"Nome": "1. Baixa Ocupação (~30%)", "Alunos_1x": int(capacidade_slots_semanais * 0.1), "Alunos_2x": int(capacidade_slots_semanais * 0.15), "Alunos_3x": int(capacidade_slots_semanais * 0.05)},
        {"Nome": "2. Ponto de Equilíbrio (~55%)", "Alunos_1x": int(capacidade_slots_semanais * 0.15), "Alunos_2x": int(capacidade_slots_semanais * 0.25), "Alunos_3x": int(capacidade_slots_semanais * 0.15)},
        {"Nome": "3. Alta Ocupação (~85%)", "Alunos_1x": int(capacidade_slots_semanais * 0.2), "Alunos_2x": int(capacidade_slots_semanais * 0.4), "Alunos_3x": int(capacidade_slots_semanais * 0.25)},
        {"Nome": "4. Capacidade Máxima (100%)", "Alunos_1x": int(capacidade_slots_semanais * 0.2), "Alunos_2x": int(capacidade_slots_semanais * 0.5), "Alunos_3x": int(capacidade_slots_semanais * 0.3)}
    ]

    dados_resultados = []
    for c in cenarios:
        total_alunos = c["Alunos_1x"] + c["Alunos_2x"] + c["Alunos_3x"]
        slots_ocupados = (c["Alunos_1x"] * 1) + (c["Alunos_2x"] * 2) + (c["Alunos_3x"] * 3)
        taxa_ocupacao = (slots_ocupados / capacidade_slots_semanais) * 100 if capacidade_slots_semanais > 0 else 0
        fat_bruto = (c["Alunos_1x"] * preco_1x) + (c["Alunos_2x"] * preco_2x) + (c["Alunos_3x"] * preco_3x)
        impostos = fat_bruto * imposto_pct
        custo_total = custos_fixos + impostos + custo_professores_mes
        lucro_liquido = fat_bruto - custo_total
        
        dados_resultados.append({
            "Cenário": c["Nome"],
            "Total Alunos": total_alunos,
            "Ocupação (%)": round(taxa_ocupacao, 1),
            "Faturamento Bruto": fat_bruto,
            "Impostos": impostos,
            "Custo Fixos": custos_fixos,
            "Comissão Professores": custo_professores_mes,
            "Custo Total": custo_total,
            "Lucro Líquido": lucro_liquido,
            "Margem Líquida (%)": round((lucro_liquido / fat_bruto * 100) if fat_bruto > 0 else 0, 1)
        })

    df = pd.DataFrame(dados_resultados)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Capacidade Máxima", f"{capacidade_slots_semanais} vagas/sem")
    m2.metric("Custo Professores", f"R$ {custo_professores_mes:,.2f}")
    m3.metric("Faturamento Máximo", f"R$ {df.iloc[-1]['Faturamento Bruto']:,.2f}")
    m4.metric("Lucro Líquido Máximo", f"R$ {df.iloc[-1]['Lucro Líquido']:,.2f}", delta=f"{df.iloc[-1]['Margem Líquida (%)']}% Margem")

    st.divider()
    st.subheader("💰 Faturamento Real (Baseado nos Clientes Cadastrados)")
    df_cadastrados_fin = carregar_clientes()
    
    if not df_cadastrados_fin.empty:
        contagem_planos = df_cadastrados_fin['plano'].value_counts()
        q_1x = contagem_planos.get("Plano 1x por semana", 0)
        q_2x = contagem_planos.get("Plano 2x por semana", 0)
        q_3x = contagem_planos.get("Plano 3x por semana", 0)
        q_ilimitado = contagem_planos.get("Plano Ilimitado", 0)
        total_cadastrados = len(df_cadastrados_fin)
        
        faturamento_real = (q_1x * preco_1x) + (q_2x * preco_2x) + (q_3x * preco_3x) + (q_ilimitado * preco_ilimitado)
        impostos_reais = faturamento_real * imposto_pct
        lucro_real = faturamento_real - (custos_fixos + impostos_reais + custo_professores_mes)

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total de Alunos", f"{total_cadastrados} alunos")
        r2.metric("Faturamento Bruto Real", f"R$ {faturamento_real:,.2f}")
        r3.metric("Impostos Reais", f"R$ {impostos_reais:,.2f}")
        r4.metric("Lucro Líquido Real", f"R$ {lucro_real:,.2f}")
    else:
        st.info("Nenhum cliente cadastrado no momento.")

# ==============================================================================
# ESTRUTURA GLOBAL DE HORÁRIOS E CÁLCULO SEGURO DE OCUPAÇÃO
# ==============================================================================
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
    ocupacao = {}
    for d in dias_semana_lista:
        for h in horarios_base:
            ocupacao[(d, h)] = 0
            
    if not df_clientes.empty:
        for _, row in df_clientes.iterrows():
            if pd.notna(row.get('dias_semana')) and pd.notna(row.get('horarios')):
                dias_cli = list(set([x.strip() for x in row['dias_semana'].split(",") if x.strip()]))
                hors_cli = list(set([x.strip() for x in row['horarios'].split(",") if x.strip()]))
                for d in dias_cli:
                    for h in hors_cli:
                        if (d, h) in ocupacao:
                            ocupacao[(d, h)] += 1
    return ocupacao

# ==============================================================================
# ABA 2: CADASTRO, EDIÇÃO, EXCLUSÃO DE CLIENTES & AGENDA
# ==============================================================================
with aba_clientes:
    st.header("📋 Agendamento e Gestão de Clientes")
    
    sub_aba_novo, sub_aba_gerenciar = st.tabs(["➕ Novo Cadastro", "✏️ Editar / Excluir Clientes"])

    with sub_aba_novo:
        if "msg_sucesso_cad" in st.session_state:
            st.success(st.session_state.msg_sucesso_cad)
            del st.session_state.msg_sucesso_cad

        if "form_reset" not in st.session_state:
            st.session_state.form_reset = False

        if "uploader_key" not in st.session_state:
            st.session_state.uploader_key = 0

        if st.session_state.form_reset:
            st.session_state.cad_cpf = ""
            st.session_state.cad_nome = ""
            st.session_state.cad_email = ""
            st.session_state.cad_nasc = ""
            st.session_state.cad_end = ""
            st.session_state.cad_tel = ""
            st.session_state.cad_nome_emerg = ""
            st.session_state.cad_tel_emerg = ""
            st.session_state.cad_obj = ""
            st.session_state.cad_tit_doc = ""
            st.session_state.cad_desc_doc = ""
            st.session_state.cad_dias_multiselect = []
            st.session_state.form_reset = False

        df_atual_clientes = carregar_clientes()
        vagas_limite = vagas_por_turma
        ocupacao_matriz = calcular_ocupacao_matriz(df_atual_clientes, vagas_limite)

        col_form, col_lista = st.columns([1, 2])
        
        with col_form:
            st.subheader("Novo Cadastro & Agendamento")
            
            raw_cpf = st.text_input("CPF (ID do Paciente)*", placeholder="000.000.000-00", key="cad_cpf")
            nome = st.text_input("Nome Completo*", key="cad_nome").upper()
            email = st.text_input("E-mail", placeholder="exemplo@email.com", key="cad_email").lower()
            
            raw_nasc = st.text_input("Data de Nascimento (DD/MM/AAAA)", placeholder="Ex: 15/08/1990", key="cad_nasc")
            endereco = st.text_input("Endereço", key="cad_end").upper()
            
            col_tel1, col_tel2 = st.columns(2)
            with col_tel1:
                raw_tel = st.text_input("Telefone / WhatsApp", key="cad_tel")
            with col_tel2:
                nome_emerg = st.text_input("Nome Contato de Emergência", placeholder="Nome", key="cad_nome_emerg").upper()

            raw_tel_emerg = st.text_input("Telefone Contato de Emergência", placeholder="(00) 00000-0000", key="cad_tel_emerg")
            
            objetivo = st.text_area("Objetivo Clínico / Diagnóstico / Restrições", key="cad_obj").upper()
            plano = st.selectbox("Plano Contratado", ["Plano 1x por semana", "Plano 2x por semana", "Plano 3x por semana", "Plano Ilimitado"], key="cad_plano")
            
            st.markdown("---")
            st.markdown("📎 **Receita Médica / Laudo Inicial (Tarefa da Secretaria)**")
            origem_doc_cad = st.selectbox("Canal de Recebimento", ["Scanner / Arquivo Local", "E-mail da Clínica", "Entrega Física / Outros"], key="cad_origem")
            titulo_doc_cad = st.text_input("Título do Laudo / Receita", placeholder="Ex: Laudo Ortopédico Joelho", key="cad_tit_doc")
            desc_doc_cad = st.text_area("Observações sobre o Laudo / Receita", placeholder="Ex: Restrição de impacto...", key="cad_desc_doc")
            
            # Uploader dinâmico que limpa junto com o formulário
            arquivo_cad = st.file_uploader(
                "Anexar Arquivo (PDF, Imagem PNG/JPG)", 
                type=["pdf", "png", "jpg", "jpeg"], 
                key=f"cad_arq_{st.session_state.uploader_key}"
            )

            st.markdown("---")
            st.markdown(f"📅 **Agenda Individual por Dia (Limite por Turma: {vagas_limite} vagas)**")
            
            dias_escolhidos = st.multiselect("Selecione o(s) Dia(s) da Semana da Aula", dias_semana_lista, key="cad_dias_multiselect")
            
            horarios_por_dia_escolhido = []
            tem_algum_dia_sem_vaga = False
            
            if dias_escolhidos:
                st.markdown("🕒 **Defina o horário disponível para cada dia selecionado:**")
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
                        st.error(f"⚠️ Todas as turmas do dia **{dia}** estão esgotadas!")
                        tem_algum_dia_sem_vaga = True
                    else:
                        escolha_rotulo = st.selectbox(f"Horário para **{dia}**:", opcoes_dia, key=f"horario_dinamico_{dia}")
                        horarios_por_dia_escolhido.append(mapa_rotulos[escolha_rotulo])
            else:
                st.info("👈 Selecione os dias da semana acima para escolher os horários correspondentes.")

            st.markdown("")
            btn_salvar_cli = st.button("💾 Salvar e Confirmar Agendamento", type="primary", key="btn_salvar_novo_cliente")
            
            if btn_salvar_cli:
                cpf = formatar_cpf(raw_cpf)
                telefone = formatar_telefone(raw_tel)
                tel_emerg = formatar_telefone(raw_tel_emerg)
                contato_emergencia = f"{nome_emerg} — {tel_emerg}" if nome_emerg or raw_tel_emerg else ""
                data_nasc = formatar_data(raw_nasc)
                
                idade_calculada = 0
                if len(data_nasc) == 10:
                    try:
                        dt = datetime.strptime(data_nasc, "%d/%m/%Y").date()
                        hoje = date.today()
                        idade_calculada = hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
                    except ValueError:
                        pass

                if not cpf.strip() or not nome.strip():
                    st.warning("Preencha o CPF e o Nome Completo.")
                elif not dias_escolhidos:
                    st.warning("Selecione pelo menos um dia da semana.")
                elif tem_algum_dia_sem_vaga:
                    st.error("⚠️ Não é possível salvar pois há dias selecionados sem vagas disponíveis.")
                elif len(horarios_por_dia_escolhido) != len(dias_escolhidos):
                    st.warning("Selecione um horário válido para cada dia escolhido.")
                else:
                    sucesso, msg = adicionar_cliente(cpf, nome, email, data_nasc, idade_calculada, endereco, telefone, contato_emergencia, objetivo, plano, dias_escolhidos, horarios_por_dia_escolhido)
                    if sucesso:
                        data_hora_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
                        if arquivo_cad is not None or titulo_doc_cad.strip():
                            nome_arq = arquivo_cad.name if arquivo_cad is not None else "Sem arquivo anexado"
                            bin_arq = arquivo_cad.read() if arquivo_cad is not None else None
                            adicionar_receita_laudo(
                                cpf=cpf,
                                data_hora=data_hora_atual,
                                titulo=titulo_doc_cad if titulo_doc_cad.strip() else "Laudo Inicial",
                                origem=origem_doc_cad,
                                descricao=desc_doc_cad,
                                nome_arq=nome_arq,
                                bin_arq=bin_arq
                            )
                        
                        st.session_state.form_reset = True
                        st.session_state.uploader_key += 1  # Reseta e limpa o uploader de arquivos
                        st.session_state.msg_sucesso_cad = "🎉 Cadastro realizado com Sucesso!"
                        st.rerun()
                    else:
                        st.error(msg)

        with col_lista:
            st.subheader("👥 Clientes Cadastrados")
            if not df_atual_clientes.empty:
                busca = st.text_input("🔍 Buscar cliente por nome ou CPF:", "", key="busca_cliente_tab")
                df_exibicao = df_atual_clientes.copy()
                if busca:
                    df_exibicao = df_exibicao[
                        df_exibicao['nome'].str.contains(busca, case=False, na=False) | 
                        df_exibicao['cpf'].str.contains(busca, case=False, na=False)
                    ]
                st.dataframe(df_exibicao, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum cliente cadastrado.")

    with sub_aba_gerenciar:
        st.subheader("✏️ Editar ou Excluir Cadastro de Clientes")
        
        with st.expander("⚠️ Opções Avançadas (Zerar Base de Dados)"):
            if st.button("🧹 Excluir TODOS os Clientes (Zerar Banco e Reiniciar IDs)", type="secondary"):
                limpa_todos_clientes()
                st.success("Todos os clientes foram excluídos e o contador de ID foi resetado para 1!")
                st.rerun()

        df_cli_gerir = carregar_clientes()
        
        if not df_cli_gerir.empty:
            lista_clientes_editar = [f"{row['nome']} (CPF: {row['cpf']})" for _, row in df_cli_gerir.iterrows()]
            escolha_cli = st.selectbox("Selecione o cliente para gerenciar:", lista_clientes_editar, key="select_cli_edit")
            
            cpf_selecionado = escolha_cli.split("CPF: ")[1].split(")")[0]
            cliente_dados = df_cli_gerir[df_cli_gerir['cpf'] == cpf_selecionado].iloc[0]
            
            with st.form("form_edicao_cliente"):
                st.markdown(f"**Editando cadastro de:** {cliente_dados['nome']} (CPF: {cliente_dados['cpf']})")
                
                novo_nome = st.text_input("Nome Completo", value=cliente_dados.get('nome', '')).upper()
                novo_email = st.text_input("E-mail", value=cliente_dados.get('email', '') if pd.notna(cliente_dados.get('email')) else '').lower()
                
                idade_val_bruta = cliente_dados.get('idade', 30)
                try:
                    idade_val_int = int(idade_val_bruta) if pd.notna(idade_val_bruta) else 30
                except (ValueError, TypeError):
                    idade_val_int = 30
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    raw_nasc_edit = st.text_input("Data de Nascimento (DD/MM/AAAA)", value=cliente_dados.get('data_nascimento', '') if pd.notna(cliente_dados.get('data_nascimento')) else '')
                    nova_data_nasc = formatar_data(raw_nasc_edit)
                with col_e2:
                    nova_idade = st.number_input("Idade", min_value=0, max_value=120, value=max(0, idade_val_int))

                novo_endereco = st.text_input("Endereço", value=cliente_dados.get('endereco', '') if pd.notna(cliente_dados.get('endereco')) else '').upper()
                
                col_e3, col_e4 = st.columns(2)
                with col_e3:
                    novo_tel = st.text_input("Telefone / WhatsApp", value=cliente_dados.get('telefone', '') if pd.notna(cliente_dados.get('telefone')) else '')
                with col_e4:
                    novo_emerg = st.text_input("Contato de Emergência", value=cliente_dados.get('contato_emergencia', '') if pd.notna(cliente_dados.get('contato_emergencia')) else '').upper()

                novo_obj = st.text_area("Objetivo Clínico / Restrições", value=cliente_dados.get('objetivo', '') if pd.notna(cliente_dados.get('objetivo')) else '').upper()
                
                planos_disp = ["Plano 1x por semana", "Plano 2x por semana", "Plano 3x por semana", "Plano Ilimitado"]
                plano_atual = cliente_dados.get('plano', 'Plano 1x por semana')
                idx_plano = planos_disp.index(plano_atual) if plano_atual in planos_disp else 0
                novo_plano = st.selectbox("Plano Contratado", planos_disp, index=idx_plano)
                
                dias_atuais_str = cliente_dados.get('dias_semana', '')
                dias_atuais_lista = [d.strip() for d in dias_atuais_str.split(",")] if pd.notna(dias_atuais_str) and dias_atuais_str else []
                novos_dias = st.multiselect("Dias da Semana da Aula", dias_semana_lista, default=[d for d in dias_atuais_lista if d in dias_semana_lista])
                
                horarios_atuais_str = cliente_dados.get('horarios', '')
                novos_horarios = [h.strip() for h in horarios_atuais_str.split(",")] if pd.notna(horarios_atuais_str) and horarios_atuais_str else ["08:00"]

                col_btn_salvar, col_btn_del = st.columns(2)
                with col_btn_salvar:
                    btn_atualizar = st.form_submit_button("💾 Salvar Alterações", type="primary")
                with col_btn_del:
                    btn_excluir = st.form_submit_button("🗑️ Excluir Cliente", type="secondary")

                if btn_atualizar:
                    atualizar_cliente(
                        cpf_antigo=cpf_selecionado,
                        nome=novo_nome,
                        email=novo_email,
                        data_nasc=nova_data_nasc,
                        idade=nova_idade,
                        endereco=novo_endereco,
                        telefone=novo_tel,
                        contato_emergencia=novo_emerg,
                        objetivo=novo_obj,
                        plano=novo_plano,
                        dias_semana=novos_dias,
                        horarios=novos_horarios
                    )
                    st.success("Cadastro do cliente atualizado com sucesso!")
                    st.rerun()

                if btn_excluir:
                    deletar_cliente(cpf_selecionado)
                    st.success("Cliente excluído com sucesso!")
                    st.rerun()
        else:
            st.info("Nenhum cliente cadastrado para gerenciar.")

# ==============================================================================
# ABA 3: MAPA VISUAL DE OCUPAÇÃO DAS TURMAS
# ==============================================================================
with aba_mapa:
    st.header("🧩 Mapa de Ocupação das Turmas")
    st.markdown("Visualização em tempo real das vagas e alunos agendados em cada horário.")
    
    df_mapa_clientes = carregar_clientes()
    limite_vagas_mapa = vagas_por_turma
    matriz = calcular_ocupacao_matriz(df_mapa_clientes, limite_vagas_mapa)
    
    col_leg1, col_leg2, col_leg3 = st.columns(3)
    col_leg1.markdown("🟢 **Vaga Disponível**")
    col_leg2.markdown("🧘‍♀️ **Aluno Agendado (Vaga Ocupada)**")
    col_leg3.markdown(f"⚙️ **Capacidade:** {limite_vagas_mapa} aluno(s) por turma")
    
    st.divider()
    
    for dia in dias_semana_lista:
        st.subheader(f"📅 {dia}")
        cols_horarios = st.columns(len(horarios_base))
        
        for idx, h in enumerate(horarios_base):
            qtd_ocupados = matriz.get((dia, h), 0)
            qtd_livres = max(0, limite_vagas_mapa - qtd_ocupados)
            
            with cols_horarios[idx]:
                assentos_html = ""
                for _ in range(qtd_ocupados):
                    assentos_html += "🧘‍♀️ "
                for _ in range(qtd_livres):
                    assentos_html += "🟢 "
                
                status_cor = "green" if qtd_livres > 0 else "red"
                st.markdown(f"**{h}**")
                st.markdown(assentos_html)
                st.caption(f":{status_cor}[{qtd_ocupados}/{limite_vagas_mapa} vagas]")
        st.markdown("---")

# ==============================================================================
# ABA 4: CADASTRO, EDIÇÃO E EXCLUSÃO DE PROFISSIONAIS
# ==============================================================================
with aba_profissionais:
    st.header("👩‍⚕️ Gestão de Fisioterapeutas e Profissionais")
    
    sub_aba_p_novo, sub_aba_p_gerir = st.tabs(["➕ Novo Profissional", "✏️ Editar / Excluir Profissionais"])
    
    with sub_aba_p_novo:
        col_p1, col_p2 = st.columns([1, 2])
        
        with col_p1:
            st.subheader("Novo Profissional")
            with st.form("form_prof", clear_on_submit=True):
                nome_prof = st.text_input("Nome do Profissional*").upper()
                conselho = st.selectbox("Conselho", ["CREFITO", "CREF", "Outro"])
                registro = st.text_input("Número do Registro (Ex: 123456-F)*").upper()
                
                btn_cad_prof = st.form_submit_button("💾 Salvar Profissional")
                if btn_cad_prof:
                    if nome_prof.strip() and registro.strip():
                        adicionar_profissional(nome_prof, conselho, registro)
                        st.success(f"Profissional **{nome_prof}** cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.warning("Preencha o nome e o registro profissional.")
                        
        with col_p2:
            st.subheader("Profissionais Cadastrados")
            df_profs = carregar_profissionais()
            if not df_profs.empty:
                st.dataframe(df_profs, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum profissional cadastrado.")

    with sub_aba_p_gerir:
        st.subheader("✏️ Editar ou Excluir Profissionais")
        df_profs_gerir = carregar_profissionais()
        
        if not df_profs_gerir.empty:
            lista_profs_edit = [f"{row['nome_prof']} ({row['conselho']}: {row['registro']}) [ID: {row['id']}]" for _, row in df_profs_gerir.iterrows()]
            escolha_prof = st.selectbox("Selecione o profissional para gerenciar:", lista_profs_edit, key="select_prof_edit")
            
            prof_id_sel = int(escolha_prof.split("[ID: ")[1].split("]")[0])
            prof_dados = df_profs_gerir[df_profs_gerir['id'] == prof_id_sel].iloc[0]
            
            with st.form("form_edicao_prof"):
                st.markdown(f"**Editando profissional ID {prof_id_sel}**")
                
                p_nome = st.text_input("Nome do Profissional", value=prof_dados['nome_prof']).upper()
                
                conselhos_disp = ["CREFITO", "CREF", "Outro"]
                c_atual = prof_dados['conselho']
                idx_c = conselhos_disp.index(c_atual) if c_atual in conselhos_disp else 0
                p_conselho = st.selectbox("Conselho", conselhos_disp, index=idx_c)
                
                p_registro = st.text_input("Número do Registro", value=prof_dados['registro']).upper()
                
                col_p_salvar, col_p_del = st.columns(2)
                with col_p_salvar:
                    btn_salvar_prof = st.form_submit_button("💾 Salvar Alterações", type="primary")
                with col_p_del:
                    btn_del_prof = st.form_submit_button("🗑️ Excluir Profissional", type="secondary")

                if btn_salvar_prof:
                    atualizar_profissional(prof_id_sel, p_nome, p_conselho, p_registro)
                    st.success("Profissional atualizado com sucesso!")
                    st.rerun()

                if btn_del_prof:
                    deletar_profissional(prof_id_sel)
                    st.success("Profissional excluído com sucesso!")
                    st.rerun()
        else:
            st.info("Nenhum profissional cadastrado para gerenciar.")

# ==============================================================================
# ABA 5: PRONTUÁRIO ELETRÔNICO & LAUDOS/RECEITAS
# ==============================================================================
with aba_prontuario:
    st.header("📝 Prontuário Eletrônico & Gestão de Laudos/Receitas")
    
    df_clientes_pront = carregar_clientes()
    df_profs_pront = carregar_profissionais()
    
    if df_clientes_pront.empty:
        st.warning("Cadastre pelo menos um cliente na aba de 'Agendamento & Clientes' para acessar os prontuários.")
    elif df_profs_pront.empty:
        st.warning("Cadastre pelo menos um profissional na aba de 'Profissionais' para assinar os atendimentos.")
    else:
        lista_pacientes = [f"{row['nome']} (CPF: {row['cpf']})" for _, row in df_clientes_pront.iterrows()]
        paciente_selecionado = st.selectbox("Selecione o Paciente", lista_pacientes, key="select_pac_prontuario")
        
        cpf_atual = paciente_selecionado.split("CPF: ")[1].split(")")[0]
        dados_paciente = df_clientes_pront[df_clientes_pront['cpf'] == cpf_atual].iloc[0]
        nome_paciente_ativo = dados_paciente.get('nome', '')
        
        with st.expander("📌 Ver Dados Cadastrais, Plano e Anexos do Paciente", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Nome:** {nome_paciente_ativo}")
            c1.write(f"**E-mail:** {dados_paciente.get('email', '-')}")
            c1.write(f"**Idade / Nasc:** {dados_paciente.get('idade', '-')} anos ({dados_paciente.get('data_nascimento', '-')})")
            c2.write(f"**Telefone:** {dados_paciente.get('telefone', '-')}")
            c2.write(f"**Emergência:** {dados_paciente.get('contato_emergencia', '-')}")
            c2.write(f"**Plano:** {dados_paciente.get('plano', '-')}")
            c3.write(f"**Dias/Horários:** {dados_paciente.get('dias_semana', '-')} às {dados_paciente.get('horarios', '-')}")
            st.write(f"**Objetivo Clínico / Restrições:** {dados_paciente.get('objetivo', '-')}")

        st.divider()

        sub_pront_evolução, sub_pront_laudos = st.tabs(["💬 Evoluções Clínicas & Atendimentos", "📁 Receitas Médicas, Laudos & Anexos"])

        with sub_pront_evolução:
            col_evolucao_form, col_evolucao_hist = st.columns([1, 1])
            
            with col_evolucao_form:
                st.subheader("➕ Registrar Nova Evolução / Consulta")
                with st.form("form_evolucao", clear_on_submit=True):
                    data_atendimento_input = st.date_input("Data da Consulta", value=datetime.today(), format="DD/MM/YYYY")
                    
                    lista_nomes_profs = [f"{r['nome_prof']} ({r['conselho']}: {r['registro']})" for _, r in df_profs_pront.iterrows()]
                    prof_responsavel = st.selectbox("Profissional Responsável", lista_nomes_profs)
                    
                    atividades = st.text_area("Atividades Realizadas / Exercícios Aplicados", placeholder="Ex: Aparelho Reformer...").upper()
                    evolucao = st.text_area("Evolução Clínica / Observações do Paciente", placeholder="Ex: Paciente relatou melhora...").upper()
                    
                    btn_salvar_pront = st.form_submit_button("💾 Salvar Prontuário")
                    
                    if btn_salvar_pront:
                        if not atividades.strip() or not evolucao.strip():
                            st.warning("Preencha as atividades e a evolução clínica.")
                        else:
                            data_hora_reg = f"{data_atendimento_input.strftime('%d/%m/%Y')} às {datetime.now().strftime('%H:%M')}"
                            adicionar_prontuario(
                                cpf=cpf_atual,
                                data_hora=data_hora_reg,
                                profissional=prof_responsavel,
                                atividades=atividades,
                                evolucao=evolucao
                            )
                            st.success("Evolução registrada com sucesso no prontuário!")
                            st.rerun()
                            
            with col_evolucao_hist:
                st.subheader("📖 Histórico de Atendimentos")
                df_historico = carregar_prontuarios(cpf_atual)
                
                if not df_historico.empty:
                    for _, hist in df_historico.iterrows():
                        with st.container(border=True):
                            st.markdown(f"👤 **Paciente:** {nome_paciente_ativo}")
                            st.markdown(f"📅 **Data/Hora:** {hist['data_atendimento']} | 👩‍⚕️ **Profissional:** {hist['profissional']}")
                            st.markdown(f"🏋️ **Atividades:** {hist['atividades']}")
                            st.markdown(f"📝 **Evolução:** {hist['evolucao']}")
                            
                            c_edit, c_del = st.columns(2)
                            with c_edit:
                                with st.popover("✏️ Editar Evolução"):
                                    with st.form(f"form_edit_ev_{hist['id']}"):
                                        novas_ativ = st.text_area("Editar Atividades", value=hist['atividades']).upper()
                                        nova_ev = st.text_area("Editar Evolução", value=hist['evolucao']).upper()
                                        if st.form_submit_button("💾 Salvar Alterações"):
                                            atualizar_prontuario(hist['id'], novas_ativ, nova_ev)
                                            st.success("Atendimento atualizado com sucesso!")
                                            st.rerun()
                            with c_del:
                                if st.button("🗑️ Excluir Atendimento", key=f"del_pront_{hist['id']}"):
                                    deletar_prontuario(hist['id'])
                                    st.success("Registro excluído!")
                                    st.rerun()
                else:
                    st.info("Nenhum registro de atendimento encontrado para este paciente.")

        with sub_pront_laudos:
            st.subheader("📂 Gestão, Incremento e Atualização de Laudos e Receitas")
            st.caption(f"Gerenciando documentos para o paciente: **{nome_paciente_ativo}**")

            col_form_laudo, col_lista_laudos = st.columns([1, 1])

            with col_form_laudo:
                with st.form(f"form_novo_laudo_{cpf_atual}", clear_on_submit=True):
                    st.markdown("**➕ Adicionar / Incrementar Novo Laudo ou Receita**")
                    origem_doc = st.selectbox("Origem do Documento", ["Scanner / Arquivo Local", "E-mail da Clínica", "Entrega Física / Outros"])
                    titulo_doc = st.text_input("Título / Descrição do Laudo", placeholder="Ex: Ressonância Magnética Atualizada")
                    obs_doc = st.text_area("Detalhes Clínicos ou Observações", placeholder="Ex: Indicado repouso parcial...")
                    arquivo_up = st.file_uploader("Arquivo Anexo (PDF, Imagem PNG/JPG)", type=["pdf", "png", "jpg", "jpeg"])

                    btn_salvar_laudo = st.form_submit_button("💾 Enviar e Anexar Documento")
                    if btn_salvar_laudo:
                        if not titulo_doc.strip():
                            st.warning("Informe o título do laudo ou receita.")
                        else:
                            nome_arq = arquivo_up.name if arquivo_up is not None else "Sem arquivo anexado"
                            bin_arq = arquivo_up.read() if arquivo_up is not None else None
                            data_hora_doc = datetime.now().strftime("%d/%m/%Y às %H:%M")
                            
                            adicionar_receita_laudo(
                                cpf=cpf_atual,
                                data_hora=data_hora_doc,
                                titulo=titulo_doc,
                                origem=origem_doc,
                                descricao=obs_doc,
                                nome_arq=nome_arq,
                                bin_arq=bin_arq
                            )
                            st.success("Laudo/Receita anexado com sucesso ao prontuário do paciente!")
                            st.rerun()

            with col_lista_laudos:
                st.subheader("📑 Documentos e Laudos Armazenados")
                df_laudos_cli = carregar_receitas_laudos(cpf_atual)

                if not df_laudos_cli.empty:
                    for _, doc in df_laudos_cli.iterrows():
                        with st.container(border=True):
                            st.markdown(f"📌 **{doc['titulo']}**")
                            st.markdown(f"👤 **Paciente:** {nome_paciente_ativo}")
                            st.caption(f"📅 Registrado em: {doc['data_recebimento']} | 📥 Origem: {doc['origem']}")
                            if pd.notna(doc['descricao_conteudo']) and doc['descricao_conteudo']:
                                st.write(f"💬 **Obs:** {doc['descricao_conteudo']}")
                            st.write(f"📎 **Arquivo:** {doc['nome_arquivo']}")
                            
                            binario_arquivo = doc.get('arquivo_bin')
                            nome_arquivo_doc = doc.get('nome_arquivo', 'documento')
                            
                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                if binario_arquivo is not None and len(binario_arquivo) > 0:
                                    b64 = base64.b64encode(binario_arquivo).decode()
                                    
                                    ext_arq = nome_arquivo_doc.split('.')[-1].lower()
                                    mime_map = {'pdf': 'application/pdf', 'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}
                                    mime_type_val = mime_map.get(ext_arq, 'application/octet-stream')
                                    
                                    href = f'<a href="data:{mime_type_val};base64,{b64}" download="{nome_arquivo_doc}" target="_blank" style="text-decoration:none;"><button style="background-color:#2d6a4f; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; font-weight:600; font-size:0.85rem;">👁️ Exibir / Baixar</button></a>'
                                    st.markdown(href, unsafe_allow_html=True)
                                else:
                                    st.caption("ℹ️ Sem arquivo binário.")
                            
                            with col_b2:
                                if st.button("🗑️ Excluir Documento", key=f"del_doc_{doc['id']}_{cpf_atual}"):
                                    deletar_receita_laudo(doc['id'])
                                    st.success("Documento removido com sucesso!")
                                    st.rerun()
                else:
                    st.info("Nenhum laudo ou receita médica anexado para este paciente até o momento.")
