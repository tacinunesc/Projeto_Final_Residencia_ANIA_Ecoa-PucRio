import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re
import unicodedata
from pathlib import Path

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Ecoa Rio | Cursos 2027",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilo customizado CSS para melhorar o visual
st.markdown(
    """
    <style>
    :root {
        --eco-ink: #15233a;
        --eco-muted: #64748b;
        --eco-line: #e2e8f0;
        --eco-teal: #0f9f91;
        --eco-navy: #10243a;
    }
    .stApp {
        background: #f4f7fb;
        color: var(--eco-ink);
    }
    [data-testid="stAppViewContainer"] .main .block-container {
        max-width: 1440px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--eco-line);
    }
    h1, h2, h3 {
        color: var(--eco-ink);
        letter-spacing: -0.025em;
    }
    .eco-hero {
        background: linear-gradient(120deg, #10243a, #173c56 65%, #0d766e);
        color: #ffffff;
        border-radius: 22px;
        padding: 30px 34px;
        margin: 0 0 24px;
        box-shadow: 0 10px 28px rgba(15, 35, 60, 0.12);
    }
    .eco-hero .eyebrow {
        color: #9be7df;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .13em;
        text-transform: uppercase;
    }
    .eco-hero h1 {
        color: #ffffff;
        font-size: clamp(28px, 3vw, 42px);
        line-height: 1.12;
        margin: 10px 0;
    }
    .eco-hero p {
        color: #d4e4ef;
        font-size: 15px;
        margin: 0;
        max-width: 900px;
    }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid var(--eco-line);
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 5px 18px rgba(15, 35, 60, 0.05);
    }
    [data-testid="stMetricLabel"] {
        color: var(--eco-muted);
        font-weight: 700;
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--eco-line);
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 10px 10px 0 0;
        font-weight: 700;
        color: #475569;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #087f73;
        border-bottom-color: var(--eco-teal);
    }
    div[data-testid="stPlotlyChart"],
    div[data-testid="stDataFrame"] {
        background: #ffffff;
        border: 1px solid var(--eco-line);
        border-radius: 16px;
        padding: 8px;
        box-shadow: 0 5px 18px rgba(15, 35, 60, 0.04);
    }
    div[data-testid="stAlert"] {
        border-radius: 12px;
    }
    @media (max-width: 700px) {
        .eco-hero {
            padding: 24px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor).replace("\ufffd", ""))
    return "".join(caractere for caractere in texto if not unicodedata.combining(caractere)).lower().strip()


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def competencia_proxy_ocupacao(ocupacao):
    nome = normalizar_texto(ocupacao)
    if "engenheiro de aplicativos" in nome:
        return "Engenharia de aplicações"
    if "desenvolvimento de sistemas" in nome:
        return "Engenharia e desenvolvimento de software"
    if "desenvolvedor de sistemas" in nome:
        return "Programação e desenvolvimento de sistemas"
    if "banco de dados" in nome:
        return "Administração e gestão de bancos de dados"
    if "redes" in nome:
        return "Redes e comunicação de dados"
    if "sistemas operacionais" in nome:
        return "Administração de sistemas e infraestrutura"
    if "suporte ao usuario" in nome:
        return "Suporte técnico ao usuário"
    if "suporte computacional" in nome:
        return "Suporte e operação computacional"
    return "Competência não classificada pelo título CBO"


def padronizar_rais(dados):
    aliases = {
        "ano": "Ano",
        "uf": "UF",
        "codigo cnae": "Codigo_CNAE",
        "cdigo cnae": "Codigo_CNAE",
        "cnae codigo": "Codigo_CNAE",
        "cnae": "Setor_CNAE",
        "setor cnae": "Setor_CNAE",
        "setor": "Setor_CNAE",
        "ocupacao cbo": "Ocupacao_CBO",
        "ocupao cbo": "Ocupacao_CBO",
        "ocupacao": "Ocupacao_CBO",
        "cbo": "Ocupacao_CBO",
        "grau de instrucao": "Grau_Instrucao",
        "grau de instruo": "Grau_Instrucao",
        "grau instrucao": "Grau_Instrucao",
        "sexo": "Sexo",
        "vinculo ativo 31 12": "Vinculo_Ativo",
        "vnculo ativo 31 12": "Vinculo_Ativo",
        "vinculo ativo": "Vinculo_Ativo",
        "quantidade de vinculos": "Qtd_Vinculos",
        "quantidade de vnculos": "Qtd_Vinculos",
        "qtd vinculos": "Qtd_Vinculos",
        "remuneracao media r": "Remuneracao_Media",
        "remuneracao mdia r": "Remuneracao_Media",
        "remuneracao media": "Remuneracao_Media",
        "salario": "Remuneracao_Media",
    }
    renomear = {}
    for coluna in dados.columns:
        chave = re.sub(r"[^a-z0-9]+", " ", normalizar_texto(coluna)).strip()
        if chave in aliases:
            renomear[coluna] = aliases[chave]
    return dados.rename(columns=renomear)


def regiao_por_uf(uf):
    regioes_por_uf = {
        "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
        "RO": "Norte", "RR": "Norte", "TO": "Norte",
        "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
        "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
        "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
        "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
        "PR": "Sul", "RS": "Sul", "SC": "Sul",
    }
    return regioes_por_uf.get(str(uf).upper(), "Não informado")


def agregar_rais(dados):
    base = dados.copy()
    base["Regiao"] = base["UF"].map(regiao_por_uf)
    quantidade = pd.to_numeric(base["Qtd_Vinculos"], errors="coerce").fillna(0)
    ativo = pd.to_numeric(base.get("Vinculo_Ativo", 1), errors="coerce")
    if not isinstance(ativo, pd.Series):
        ativo = pd.Series(ativo, index=base.index)
    base["Vinculos_Ativos"] = quantidade * ativo.fillna(1).clip(lower=0, upper=1)
    base["Codigo_CNAE"] = base.get("Codigo_CNAE", "00000").astype(str).str.replace(r"\.0$", "", regex=True)
    base["CNAE_Divisao"] = base["Codigo_CNAE"].str.zfill(5).str[:2]
    base["Massa_Salarial"] = (
        pd.to_numeric(base["Remuneracao_Media"], errors="coerce").fillna(0)
        * base["Vinculos_Ativos"]
    )
    niveis_superiores = {
        "ensino superior completo",
        "mestrado completo",
        "doutorado completo",
        "especializacao completa",
        "pos graduacao completa",
    }
    base["Vinculos_Superior_Pos"] = np.where(
        base["Grau_Instrucao"].map(normalizar_texto).isin(niveis_superiores),
        base["Vinculos_Ativos"],
        0,
    )
    chaves = ["Ano", "Regiao", "UF", "CNAE_Divisao", "Setor_CNAE", "Ocupacao_CBO"]
    agregado = base.groupby(chaves, as_index=False, dropna=False).agg(
        Total_Vinculos_Ativos=("Vinculos_Ativos", "sum"),
        Massa_Salarial=("Massa_Salarial", "sum"),
        Vinculos_Superior_Pos=("Vinculos_Superior_Pos", "sum"),
    )
    denominador = agregado["Total_Vinculos_Ativos"].replace(0, np.nan)
    agregado["Remuneracao_Media_Ativos"] = agregado["Massa_Salarial"] / denominador
    agregado["Proporcao_Superior_Pos_pct"] = agregado["Vinculos_Superior_Pos"] / denominador * 100
    return agregado.drop(columns="Massa_Salarial").fillna(
        {"Remuneracao_Media_Ativos": 0, "Proporcao_Superior_Pos_pct": 0}
    )


def normalizar_setor_tic(setor):
    chave = normalizar_texto(setor)
    codigos = {
        "1": "Indústria de Transformação",
        "2": "Construção",
        "3": "Comércio e reparação de veículos",
        "5": "Alojamento e Alimentação",
        "6": "Informação e Comunicação",
        "9": "Serviços",
    }
    if chave in codigos:
        return codigos[chave]
    if "industria de transformacao" in chave:
        return "Indústria de Transformação"
    if "construcao" in chave:
        return "Construção"
    if "comercio" in chave:
        return "Comércio e reparação de veículos"
    if "alojamento" in chave or "alimentacao" in chave:
        return "Alojamento e Alimentação"
    if "informacao e comunicacao" in chave:
        return "Informação e Comunicação"
    if chave == "servicos":
        return "Serviços"
    return str(setor).strip()


def divisao_cnae_tic(setor):
    chave = normalizar_texto(normalizar_setor_tic(setor))
    if "industria de transformacao" in chave:
        return "10-33"
    if "construcao" in chave:
        return "41-43"
    if "comercio" in chave:
        return "45-47"
    if "transporte" in chave:
        return "49-53"
    if "alojamento" in chave or "alimentacao" in chave:
        return "55-56"
    if "informacao e comunicacao" in chave:
        return "58-63"
    if "atividades imobiliarias" in chave or "servicos complementares" in chave:
        return "68-82 (aprox.)"
    if "artes" in chave or "recreacao" in chave or "outras atividades de servicos" in chave:
        return "90-96 (aprox.)"
    if chave == "servicos":
        return "Agregado amplo; sem divisao CNAE unica"
    return "Sem correspondencia direta identificada"


@st.cache_data(show_spinner="Lendo microdados TIC Empresas...")
def carregar_tic_empresas(diretorio, versao_arquivo=None):
    pasta = Path(diretorio)
    arquivo = pasta / "tic_empresas_2021_2025.xlsx"
    if not arquivo.exists():
        return pd.DataFrame(), pd.DataFrame(), [], pd.DataFrame()

    base = pd.read_excel(arquivo, sheet_name=0)
    colunas_normalizadas = {
        re.sub(r"[^a-z0-9]+", " ", normalizar_texto(coluna)).strip(): coluna
        for coluna in base.columns
    }
    aliases = {
        "ano da pesquisa": "Ano",
        "ano": "Ano",
        "regiao geografica": "Regiao",
        "regiao": "Regiao",
        "porte da empresa": "Porte",
        "porte": "Porte",
        "setor economico cnae": "Setor_TIC",
        "peso amostral expansao": "Peso",
        "peso amostral peso": "Peso",
        "adocao uso de inteligencia artificial": "Adotou_IA",
        "adota ia h1": "Adotou_IA",
        "existencia de especialista em ti": "Especialista_TI",
        "uso de big data analise de grandes volumes de dados": "Big_Data",
        "uso de analise avancada de dados": "Analise_Avancada",
    }
    renomear = {
        coluna: aliases[chave]
        for chave, coluna in colunas_normalizadas.items()
        if chave in aliases
    }
    base = base.rename(columns=renomear)

    familias = {
        "aquisicao de ia": ("H8", "Forma de aquisição"),
        "tipo de ia": ("H9", "Tipo de IA"),
        "aplicacao da ia": ("H10", "Aplicação da IA"),
        "barreira de ia": ("H13", "Barreira"),
    }
    rotulos_indicadores = {}
    for prefixo, (familia, _) in familias.items():
        origem = [
            (chave, coluna)
            for chave, coluna in colunas_normalizadas.items()
            if chave.startswith(prefixo)
        ]
        for indice, (chave, coluna) in enumerate(origem):
            codigo = f"{familia}_{chr(ord('A') + indice)}"
            base = base.rename(columns={coluna: codigo})
            rotulos_indicadores[codigo] = str(coluna).split(":", 1)[-1].strip()

    rotulo_pessoal = next(
        (
            coluna
            for coluna, rotulo in rotulos_indicadores.items()
            if coluna.startswith("H13_")
            and "profissionais qualificados" in normalizar_texto(rotulo)
        ),
        None,
    )
    if rotulo_pessoal:
        base["Barreira_Pessoal_Resposta_Original"] = base[rotulo_pessoal].copy()

    colunas_necessarias = {
        "Ano", "Regiao", "Porte", "Setor_TIC", "Adotou_IA", "Peso"
    }
    if not colunas_necessarias.issubset(base.columns):
        return pd.DataFrame(), pd.DataFrame(), [], pd.DataFrame()

    def converter_peso(valores):
        texto = valores.astype(str).str.strip().str.replace(",", ".", regex=False)
        return pd.to_numeric(texto, errors="coerce")

    def converter_resposta(valor):
        resposta = normalizar_texto(valor)
        if resposta in {"sim", "1"} or resposta.startswith("fator relevante"):
            return 1.0
        if resposta in {"nao", "no", "0"}:
            return 0.0
        return np.nan

    base["Ano"] = pd.to_numeric(base["Ano"], errors="coerce")
    base["Peso"] = converter_peso(base["Peso"])
    for coluna in [
        "Adotou_IA", "Especialista_TI", "Big_Data", "Analise_Avancada",
        *rotulos_indicadores,
    ]:
        if coluna in base.columns:
            base[coluna] = base[coluna].map(converter_resposta)
    base["Regiao"] = base["Regiao"].fillna("Não informado").astype(str).str.strip()
    base["Porte"] = base["Porte"].map(
        lambda valor: (
            "Pequena (10-49)"
            if str(valor).strip() == "4"
            else "Média (50-249)"
            if normalizar_texto(valor).startswith(("media", "mdia"))
            else "Grande (250+)"
            if "grande" in normalizar_texto(valor)
            else str(valor).strip()
        )
    )
    base["Setor_TIC"] = base["Setor_TIC"].map(normalizar_setor_tic)
    base = base.dropna(subset=["Ano", "Setor_TIC", "Peso"])
    base = base.loc[base["Peso"] > 0].copy()
    base["Escala_Peso_Valida"] = base.groupby("Ano")["Peso"].transform("median").between(
        0, 1_000_000
    )

    base["Barreira_Pessoal"] = (
        base[rotulo_pessoal] if rotulo_pessoal else np.nan
    )
    anos_h13_sem_resposta_positiva = sorted(
        int(ano)
        for ano, grupo in base.groupby("Ano")
        if not grupo.loc[
            grupo["Adotou_IA"].eq(0), "Barreira_Pessoal"
        ].isin([0, 1]).any()
    )

    adocao_linhas = []
    barreira_linhas = []
    agrupamentos = [
        (["Ano", "Regiao", "Porte", "Setor_TIC"], None),
        (["Ano", "Regiao", "Setor_TIC"], "Porte"),
        (["Ano", "Regiao", "Porte"], "Setor_TIC"),
        (["Ano", "Regiao"], "Porte,Setor_TIC"),
    ]
    colunas_h13 = [coluna for coluna in rotulos_indicadores if coluna.startswith("H13_")]

    for chaves, ausentes in agrupamentos:
        for valores, grupo in base.groupby(chaves, dropna=False, sort=False):
            valores = valores if isinstance(valores, tuple) else (valores,)
            identificadores = dict(zip(chaves, valores))
            ano = int(identificadores["Ano"])
            regiao = identificadores.get("Regiao", "Brasil")
            porte = identificadores.get("Porte", "Todos os portes")
            setor = identificadores.get("Setor_TIC", "Todos os setores")
            if ausentes:
                for coluna in ausentes.split(","):
                    if coluna == "Porte":
                        porte = "Todos os portes"
                    elif coluna == "Setor_TIC":
                        setor = "Todos os setores"

            respostas_adocao = grupo["Adotou_IA"].isin([0, 1])
            peso_adocao = grupo.loc[respostas_adocao, "Peso"].sum()
            if peso_adocao > 0:
                adocao_linhas.append(
                    {
                        "Ano": int(ano),
                        "Regiao": regiao,
                        "Porte": porte,
                        "Setor_TIC": setor,
                        "Divisoes_CNAE_2_0": (
                            "Agregado; sem divisão única"
                            if setor == "Todos os setores"
                            else divisao_cnae_tic(setor)
                        ),
                        "Adocao_IA_pct": (
                            grupo.loc[respostas_adocao & grupo["Adotou_IA"].eq(1), "Peso"].sum()
                            / peso_adocao
                            * 100
                        ),
                        "Peso_Adocao_Valido": peso_adocao,
                        "Empresas_Adotantes_Estimadas": grupo.loc[
                            respostas_adocao & grupo["Adotou_IA"].eq(1), "Peso"
                        ].sum(),
                        "Respostas_Adocao_Validas": int(respostas_adocao.sum()),
                        "Escala_Peso_Valida": bool(grupo["Escala_Peso_Valida"].all()),
                    }
                )

            for coluna in colunas_h13:
                nao_adotantes = grupo.loc[grupo["Adotou_IA"].eq(0)]
                validas = nao_adotantes[coluna].isin([0, 1])
                peso_valido = nao_adotantes.loc[validas, "Peso"].sum()
                if peso_valido > 0:
                    barreira_linhas.append(
                        {
                            "Ano": ano,
                            "Regiao": regiao,
                            "Porte": porte,
                            "Setor_TIC": setor,
                            "Divisoes_CNAE_2_0": divisao_cnae_tic(setor),
                            "Barreira": rotulos_indicadores[coluna],
                            "Codigo": coluna,
                            "Proporcao_pct": (
                                nao_adotantes.loc[
                                    validas & nao_adotantes[coluna].eq(1), "Peso"
                                ].sum()
                                / peso_valido
                                * 100
                            ),
                            "Empresas_Indicaram_Estimadas": nao_adotantes.loc[
                                validas & nao_adotantes[coluna].eq(1), "Peso"
                            ].sum(),
                            "Peso_Respostas_Validas": peso_valido,
                            "Respostas_Validas": int(validas.sum()),
                        }
                    )

    arquivo_consolidado = pasta / "tic_empresas_2023_2025.xlsx"
    if rotulo_pessoal and arquivo_consolidado.exists():
        base_pessoal_2025 = pd.read_excel(
            arquivo_consolidado, sheet_name="Microdados Consolidados"
        )
        colunas_pessoais_2025 = {
            "Ano": "Ano",
            "Região": "Regiao",
            "Porte": "Porte",
            "Setor Econômico (CNAE)": "Setor_TIC",
            "Adota IA (H1)": "Adotou_IA",
            "Barreira Pessoal (H13_A)": "Barreira_Pessoal",
            "Peso Amostral (PESO)": "Peso",
        }
        colunas_ausentes = set(colunas_pessoais_2025).difference(
            base_pessoal_2025.columns
        )
        if colunas_ausentes:
            raise ValueError(
                "A planilha consolidada TIC não contém as colunas esperadas para "
                "recalcular a barreira de pessoal: "
                + ", ".join(sorted(colunas_ausentes))
            )
        base_pessoal_2025 = base_pessoal_2025.rename(
            columns=colunas_pessoais_2025
        )
        base_pessoal_2025["Ano"] = pd.to_numeric(
            base_pessoal_2025["Ano"], errors="coerce"
        )
        base_pessoal_2025 = base_pessoal_2025.loc[
            base_pessoal_2025["Ano"].eq(2025)
        ].copy()
        base_pessoal_2025["Peso"] = pd.to_numeric(
            base_pessoal_2025["Peso"], errors="coerce"
        )
        base_pessoal_2025["Adotou_IA"] = pd.to_numeric(
            base_pessoal_2025["Adotou_IA"], errors="coerce"
        )
        base_pessoal_2025["Barreira_Pessoal"] = pd.to_numeric(
            base_pessoal_2025["Barreira_Pessoal"], errors="coerce"
        )
        base_pessoal_2025["Setor_TIC"] = base_pessoal_2025["Setor_TIC"].map(
            normalizar_setor_tic
        )
        base_pessoal_2025["Porte"] = base_pessoal_2025["Porte"].map(
            lambda valor: (
                "Pequena (10-49)"
                if str(valor).strip() == "4"
                else "Média (50-249)"
                if normalizar_texto(valor).startswith(("media", "mdia"))
                else "Grande (250+)"
                if "grande" in normalizar_texto(valor)
                else str(valor).strip()
            )
        )
        base_pessoal_2025 = base_pessoal_2025.dropna(
            subset=["Regiao", "Porte", "Setor_TIC", "Adotou_IA", "Peso"]
        )
        base_pessoal_2025 = base_pessoal_2025.loc[
            base_pessoal_2025["Peso"].gt(0)
            & base_pessoal_2025["Adotou_IA"].eq(0)
        ]
        agrupamentos_pessoais = [
            (["Ano", "Regiao", "Porte", "Setor_TIC"], None),
            (["Ano", "Regiao", "Setor_TIC"], "Porte"),
            (["Ano", "Regiao", "Porte"], "Setor_TIC"),
            (["Ano", "Regiao"], "Porte,Setor_TIC"),
        ]
        barreiras_2025 = []
        for chaves, ausentes in agrupamentos_pessoais:
            for valores, grupo in base_pessoal_2025.groupby(
                chaves, dropna=False, sort=False
            ):
                valores = valores if isinstance(valores, tuple) else (valores,)
                identificadores = dict(zip(chaves, valores))
                regiao = identificadores.get("Regiao", "Brasil")
                porte = identificadores.get("Porte", "Todos os portes")
                setor = identificadores.get("Setor_TIC", "Todos os setores")
                if ausentes:
                    for coluna in ausentes.split(","):
                        if coluna == "Porte":
                            porte = "Todos os portes"
                        elif coluna == "Setor_TIC":
                            setor = "Todos os setores"
                validas = grupo["Barreira_Pessoal"].isin([0, 1])
                respostas_validas = grupo.loc[validas]
                peso_valido = respostas_validas["Peso"].sum()
                if peso_valido <= 0:
                    continue
                peso_sim = respostas_validas.loc[
                    respostas_validas["Barreira_Pessoal"].eq(1), "Peso"
                ].sum()
                barreiras_2025.append(
                    {
                        "Ano": 2025,
                        "Regiao": regiao,
                        "Porte": porte,
                        "Setor_TIC": setor,
                        "Divisoes_CNAE_2_0": divisao_cnae_tic(setor),
                        "Barreira": rotulos_indicadores[rotulo_pessoal],
                        "Codigo": rotulo_pessoal,
                        "Proporcao_pct": peso_sim / peso_valido * 100,
                        "Empresas_Indicaram_Estimadas": peso_sim,
                        "Peso_Respostas_Validas": peso_valido,
                        "Respostas_Validas": int(validas.sum()),
                    }
                )
        if barreiras_2025:
            barreira_linhas = [
                linha
                for linha in barreira_linhas
                if not (
                    linha["Ano"] == 2025
                    and linha["Codigo"] == rotulo_pessoal
                )
            ]
            barreira_linhas.extend(barreiras_2025)
            anos_h13_sem_resposta_positiva = [
                ano
                for ano in anos_h13_sem_resposta_positiva
                if ano != 2025
            ]

    adocao_df = pd.DataFrame(adocao_linhas)
    adocao_df.attrs["campos_ia_disponiveis"] = (
        ["Adotou_IA"] + list(rotulos_indicadores)
    )
    adocao_df.attrs["campos_ia_ausentes"] = []
    adocao_df.attrs["grupos_h13_h14_disponiveis"] = colunas_h13
    base.attrs["rotulos_indicadores"] = rotulos_indicadores
    return (
        adocao_df,
        pd.DataFrame(barreira_linhas),
        anos_h13_sem_resposta_positiva,
        base,
    )


@st.cache_data
def carregar_dados(uploaded_file=None):
    """Carrega a base de dados ou gera um conjunto sintético para demonstração."""
    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                return pd.read_csv(uploaded_file)
            return pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo enviado: {e}")
            return None

    np.random.seed(42)
    anos = [2022, 2023, 2024, 2025]
    cbos = [
        "Analista de Desenvolvimento de Sistemas",
        "Desenvolvedor de Sistemas de Tecnologia da Informação (Técnico)",
        "Analista de Suporte Computacional",
        "Técnico de Suporte ao Usuário de Tecnologia da Informação",
        "Analista de Redes e de Comunicação de Dados",
        "Administrador de Banco de Dados",
        "Administrador de Sistemas Operacionais",
        "Engenheiro de Aplicativos em Computação",
    ]
    cnaes = [
        "Desenvolvimento de Programas sob Encomenda",
        "Suporte Técnico, Manutenção e outros Serviços em Tecnologia da Informação",
        "Consultoria em Tecnologia da Informação",
        "Desenvolvimento e Licenciamento de Programas de Computador Customizáveis",
        "Desenvolvimento e Licenciamento de Programas de Computador não-customizáveis",
        "Comércio Varejista",
        "Serviços de Escritório, Apoio Administrativo",
        "Bancos múltiplos, sem carteira comercial",
        "Educação",
        "Atividades de Sedes de Empresas e de Consultoria em Gestão Empresarial",
    ]
    graus_instrucao = [
        "Ensino Médio completo",
        "Ensino Superior completo",
        "Ensino Superior incompleto",
        "Mestrado completo",
        "Doutorado completo",
    ]

    base_sal = {
        "Analista de Desenvolvimento de Sistemas": 7500,
        "Desenvolvedor de Sistemas de Tecnologia da Informação (Técnico)": 4800,
        "Analista de Suporte Computacional": 4300,
        "Técnico de Suporte ao Usuário de Tecnologia da Informação": 2600,
        "Analista de Redes e de Comunicação de Dados": 5200,
        "Administrador de Banco de Dados": 8500,
        "Administrador de Sistemas Operacionais": 8000,
        "Engenheiro de Aplicativos em Computação": 13500,
    }

    dados = []
    for _ in range(5000):
        ano = np.random.choice(anos, p=[0.25, 0.25, 0.25, 0.25])
        cbo = np.random.choice(cbos, p=[0.30, 0.15, 0.15, 0.10, 0.10, 0.08, 0.07, 0.05])
        cnae = np.random.choice(cnaes)
        sexo = np.random.choice(["Feminino", "Masculino"], p=[0.22, 0.78])
        grau = np.random.choice(graus_instrucao, p=[0.25, 0.55, 0.15, 0.03, 0.02])

        fator_ano = 1.0 if ano == 2022 else (0.95 if ano == 2023 else (1.02 if ano == 2024 else 1.08))
        remuneracao = max(1412.0, np.random.normal(base_sal[cbo] * fator_ano, base_sal[cbo] * 0.2))

        dados.append(
            {
                "Ano": ano,
                "Ocupacao_CBO": cbo,
                "Setor_CNAE": cnae,
                "Sexo": sexo,
                "Grau_Instrucao": grau,
                "Remuneracao_Media": remuneracao,
                "Qtd_Vinculos": np.random.randint(5, 50),
            }
        )

    return pd.DataFrame(dados)


st.markdown(
    """
    <header class="eco-hero">
        <div class="eyebrow">Briefing executivo · Grupo Ecoa Rio</div>
        <h1>TRABALHO, TECNOLOGIA, IA E CURSOS PARA 2027</h1>
        <p>Uma leitura integrada da adoção de IA nas empresas e do emprego formal em tecnologia,
        com novas análises para orientar prioridades de formação.</p>
    </header>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("📁 Fonte de Dados")
uploaded_file = st.sidebar.file_uploader("Carregar ou substituir a base RAIS", type=["xlsx", "xls", "csv"])

diretorio_app = Path(__file__).resolve().parent
arquivo_rais = diretorio_app / "RAIS 2022-2025.xlsx"
arquivo_tic = diretorio_app / "tic_empresas_2021_2025.xlsx"
versao_tic = (
    (arquivo_tic.stat().st_mtime_ns, arquivo_tic.stat().st_size)
    if arquivo_tic.exists()
    else None
)
fonte_rais = uploaded_file if uploaded_file is not None else (arquivo_rais if arquivo_rais.exists() else None)
df = carregar_dados(fonte_rais)

if df is not None:
    df = padronizar_rais(df)

    colunas_criticas = {
        "Ano": 2024,
        "UF": "Não informado",
        "Codigo_CNAE": "00000",
        "Ocupacao_CBO": "Analista de Desenvolvimento de Sistemas",
        "Setor_CNAE": "Desenvolvimento de Programas sob Encomenda",
        "Sexo": "Masculino",
        "Grau_Instrucao": "Ensino Superior completo",
        "Vinculo_Ativo": 1,
        "Remuneracao_Media": 5000.0,
        "Qtd_Vinculos": 10,
    }

    for coluna, valor_padrao in colunas_criticas.items():
        if coluna not in df.columns:
            df[coluna] = valor_padrao

    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").fillna(2024).astype(int)
    df["Remuneracao_Media"] = pd.to_numeric(df["Remuneracao_Media"], errors="coerce").fillna(5000.0)
    df["Qtd_Vinculos"] = pd.to_numeric(df["Qtd_Vinculos"], errors="coerce").fillna(10)
    df["Vinculo_Ativo"] = pd.to_numeric(df["Vinculo_Ativo"], errors="coerce").fillna(1).clip(0, 1)
    df["Vinculos_Ativos"] = df["Qtd_Vinculos"] * df["Vinculo_Ativo"]

    filtro_ti = df["Ocupacao_CBO"].map(normalizar_texto).str.contains(
        r"tecnologia da informacao|sistemas|computacao|computacional|dados|software|redes|suporte",
        regex=True,
        na=False,
    )
    df = df.loc[filtro_ti].copy()

    df["Regiao"] = df["UF"].map(regiao_por_uf)
    (
        df_tic_adocao,
        df_tic_barreiras,
        anos_h13_sem_resposta_positiva,
        df_tic_microdados,
    ) = carregar_tic_empresas(
        str(diretorio_app), versao_tic
    )

    st.sidebar.divider()
    with st.sidebar.expander("Filtros RAIS", expanded=True):
        anos_rais = sorted(df["Ano"].dropna().unique().tolist())
        regioes_rais = sorted(df["Regiao"].dropna().unique().tolist())
        anos_rais_sel = st.multiselect("Ano", anos_rais, default=anos_rais, key="rais_anos")
        regioes_rais_sel = st.multiselect(
            "Região", regioes_rais, default=regioes_rais, key="rais_regioes"
        )
        ufs_opcoes = sorted(df.loc[df["Regiao"].isin(regioes_rais_sel), "UF"].dropna().unique().tolist())
        ufs_rais_sel = st.multiselect("UF", ufs_opcoes, default=ufs_opcoes, key="rais_ufs")
        ocupacoes_rais = sorted(df["Ocupacao_CBO"].dropna().unique().tolist())
        ocupacoes_rais_sel = st.multiselect(
            "Ocupação (CBO)", ocupacoes_rais, default=ocupacoes_rais, key="rais_ocupacoes"
        )
        graus_rais = sorted(df["Grau_Instrucao"].dropna().unique().tolist())
        graus_rais_sel = st.multiselect(
            "Grau de instrução", graus_rais, default=graus_rais, key="rais_graus"
        )
        setores_rais = sorted(df["Setor_CNAE"].dropna().unique().tolist())
        setores_rais_sel = st.multiselect(
            "Setor (CNAE)", setores_rais, default=setores_rais, key="rais_setores"
        )
        sexos_rais = sorted(df["Sexo"].dropna().unique().tolist())
        sexos_rais_sel = st.multiselect(
            "Sexo", sexos_rais, default=sexos_rais, key="rais_sexos"
        )

    if not df_tic_adocao.empty:
        with st.sidebar.expander("Filtros TIC Empresas", expanded=True):
            anos_tic_opcoes = sorted(df_tic_adocao["Ano"].unique().tolist())
            regioes_tic_opcoes = sorted(df_tic_adocao["Regiao"].dropna().unique().tolist())
            setores_tic_opcoes = sorted(
                df_tic_adocao.loc[
                    df_tic_adocao["Setor_TIC"] != "Todos os setores", "Setor_TIC"
                ].dropna().unique().tolist()
            )
            portes_tic_opcoes = ["Todos os portes"] + sorted(
                porte
                for porte in df_tic_adocao["Porte"].dropna().unique().tolist()
                if porte != "Todos os portes"
            )
            anos_tic_sel = st.multiselect(
                "Ano da pesquisa", anos_tic_opcoes, default=anos_tic_opcoes, key="tic_anos"
            )
            regioes_tic_sel = st.multiselect(
                "Região", regioes_tic_opcoes, default=regioes_tic_opcoes, key="tic_regioes"
            )
            setores_tic_sel = st.multiselect(
                "Setor econômico", setores_tic_opcoes, default=setores_tic_opcoes, key="tic_setores"
            )
            porte_tic_sel = st.selectbox(
                "Porte da empresa", portes_tic_opcoes, index=0, key="tic_porte"
            )
    else:
        anos_tic_sel = []
        regioes_tic_sel = []
        setores_tic_sel = []
        porte_tic_sel = "Todos os portes"

    tab_rais, tab_comparativo, tab_tic, tab_cursos = st.tabs(
        [
            "ANÁLISE DE MERCADO FORMAL",
            "COMPARATIVO FORMALXINFORMAL",
            "ADOÇÃO DE IA",
            "CURSOS 2027",
        ]
    )

    rais_visao = df.loc[
        df["Ano"].isin(anos_rais_sel)
        & df["Regiao"].isin(regioes_rais_sel)
        & df["UF"].isin(ufs_rais_sel)
        & df["Ocupacao_CBO"].isin(ocupacoes_rais_sel)
        & df["Grau_Instrucao"].isin(graus_rais_sel)
        & df["Setor_CNAE"].isin(setores_rais_sel)
        & df["Sexo"].isin(sexos_rais_sel)
    ].copy()

    with tab_rais:
        st.subheader("Emprego formal em ocupações de tecnologia")
        if rais_visao.empty:
            st.info("Não há registros para os filtros selecionados.")
        else:
            rais_agregado = agregar_rais(rais_visao)
            total_ativos = int(rais_visao["Vinculos_Ativos"].sum())
            massa_salarial = (rais_visao["Remuneracao_Media"] * rais_visao["Vinculos_Ativos"]).sum()
            media_salarial = massa_salarial / total_ativos if total_ativos else 0
            superior_pos = rais_visao["Grau_Instrucao"].map(normalizar_texto).isin(
                {
                    "ensino superior completo", "mestrado completo", "doutorado completo",
                    "especializacao completa", "pos graduacao completa",
                }
            )
            proporcao_superior = (
                rais_visao.loc[superior_pos, "Vinculos_Ativos"].sum() / total_ativos * 100
                if total_ativos else 0
            )
            metrica1, metrica2, metrica3 = st.columns(3)
            anos_rais_visao = sorted(rais_visao["Ano"].dropna().unique().tolist())
            rotulo_vinculos = (
                "Vínculos ativos em 31/12"
                if len(anos_rais_visao) == 1
                else "Vínculos ativos · soma anual"
            )
            metrica1.metric(
                rotulo_vinculos,
                f"{total_ativos:,.0f}".replace(",", "."),
                help=(
                    "Em seleções com vários anos, soma o estoque de vínculos ativos "
                    "em cada 31/12. Não representa vínculos ou pessoas únicas no período."
                ),
            )
            metrica2.metric("Remuneração média ponderada", formatar_moeda(media_salarial))
            metrica3.metric("Superior completo ou pós", f"{proporcao_superior:.1f}%")
            periodo_rais = (
                str(anos_rais_visao[0])
                if len(anos_rais_visao) == 1
                else f"{anos_rais_visao[0]}–{anos_rais_visao[-1]}"
            )
            registros_rais = f"{len(rais_visao):,}".replace(",", ".")
            st.caption(
                f"Período selecionado: {periodo_rais}. "
                f"A base contém {registros_rais} registros agregados para os filtros atuais "
                "(linhas da planilha não equivalem a trabalhadores). "
                "O total de vínculos é a soma da quantidade de vínculos multiplicada "
                "pelo indicador “Vínculo Ativo (31/12)”."
            )

            st.markdown("#### Competências com sinais de pressão potencial")
            anos_comparacao = sorted(rais_visao["Ano"].dropna().unique().tolist())
            if len(anos_comparacao) < 2:
                st.info("Selecione pelo menos dois anos para comparar estoque e remuneração.")
            else:
                rais_pressao = rais_visao.assign(
                    Massa_Salarial=rais_visao["Remuneracao_Media"] * rais_visao["Vinculos_Ativos"]
                ).groupby(["Ano", "Ocupacao_CBO"], as_index=False).agg(
                    Estoque_Ativo=("Vinculos_Ativos", "sum"),
                    Massa_Salarial=("Massa_Salarial", "sum"),
                )
                rais_pressao["Remuneracao_Ponderada"] = (
                    rais_pressao["Massa_Salarial"]
                    / rais_pressao["Estoque_Ativo"].replace(0, np.nan)
                )
                ano_inicial = anos_comparacao[0]
                ano_final = anos_comparacao[-1]
                inicial = rais_pressao.loc[
                    rais_pressao["Ano"] == ano_inicial,
                    ["Ocupacao_CBO", "Estoque_Ativo", "Remuneracao_Ponderada"],
                ].rename(
                    columns={
                        "Estoque_Ativo": "Estoque_Inicial",
                        "Remuneracao_Ponderada": "Salario_Inicial",
                    }
                )
                final = rais_pressao.loc[
                    rais_pressao["Ano"] == ano_final,
                    ["Ocupacao_CBO", "Estoque_Ativo", "Remuneracao_Ponderada"],
                ].rename(
                    columns={
                        "Estoque_Ativo": "Estoque_Final",
                        "Remuneracao_Ponderada": "Salario_Final",
                    }
                )
                comparacao_pressao = inicial.merge(final, on="Ocupacao_CBO", how="inner")
                comparacao_pressao["Variacao_Estoque_pct"] = (
                    (comparacao_pressao["Estoque_Final"] / comparacao_pressao["Estoque_Inicial"] - 1)
                    * 100
                )
                comparacao_pressao["Variacao_Salarial_Nominal_pct"] = (
                    (comparacao_pressao["Salario_Final"] / comparacao_pressao["Salario_Inicial"] - 1)
                    * 100
                )
                comparacao_pressao["Competencia_Proxy"] = comparacao_pressao[
                    "Ocupacao_CBO"
                ].map(competencia_proxy_ocupacao)
                comparacao_pressao["Sinal"] = np.select(
                    [
                        (comparacao_pressao["Variacao_Estoque_pct"] < 0)
                        & (comparacao_pressao["Variacao_Salarial_Nominal_pct"] > 0),
                        (comparacao_pressao["Variacao_Estoque_pct"] >= 0)
                        & (
                            comparacao_pressao["Variacao_Salarial_Nominal_pct"]
                            > comparacao_pressao["Variacao_Estoque_pct"]
                        ),
                    ],
                    ["Pressão potencial: estoque cai e salário sobe", "Salário cresce mais que o estoque"],
                    default="Sem sinal conjunto neste indicador",
                )
                fig_pressao = px.scatter(
                    comparacao_pressao,
                    x="Variacao_Estoque_pct",
                    y="Variacao_Salarial_Nominal_pct",
                    size="Estoque_Final",
                    color="Sinal",
                    hover_name="Competencia_Proxy",
                    hover_data={
                        "Ocupacao_CBO": True,
                        "Estoque_Inicial": ":,.0f",
                        "Estoque_Final": ":,.0f",
                        "Salario_Inicial": ":.2f",
                        "Salario_Final": ":.2f",
                    },
                    labels={
                        "Variacao_Estoque_pct": f"Variação dos vínculos ativos ({ano_inicial}-{ano_final}, %)",
                        "Variacao_Salarial_Nominal_pct": f"Variação salarial nominal ({ano_inicial}-{ano_final}, %)",
                        "Sinal": "Leitura exploratória",
                        "Estoque_Final": f"Vínculos ativos em {ano_final}",
                        "Ocupacao_CBO": "Ocupação (CBO)",
                    },
                    template="plotly_white",
                )
                fig_pressao.add_hline(y=0, line_dash="dash", line_color="#666")
                fig_pressao.add_vline(x=0, line_dash="dash", line_color="#666")
                fig_pressao.update_layout(height=520, legend_title_text="Sinal exploratório")
                st.plotly_chart(fig_pressao, use_container_width=True)
                st.caption(
                    "Compara a variação dos vínculos e dos salários por ocupação entre os anos selecionados."
                )

                st.markdown("#### Demanda observada por ocupação tecnológica")
                demanda_rais = rais_visao.groupby(
                ["Ano", "Regiao", "Ocupacao_CBO"], as_index=False
            )["Vinculos_Ativos"].sum()
            fig_demanda = px.line(
                demanda_rais,
                x="Ano",
                y="Vinculos_Ativos",
                color="Regiao",
                facet_col="Ocupacao_CBO",
                facet_col_wrap=2,
                markers=True,
                labels={
                    "Ano": "Ano",
                    "Vinculos_Ativos": "Vínculos ativos",
                    "Ocupacao_CBO": "Ocupação (CBO)",
                    "Regiao": "Região",
                },
                template="plotly_white",
            )
            fig_demanda.update_yaxes(matches=None, rangemode="tozero")
            fig_demanda.update_layout(height=1200, legend_title_text="Região")
            st.plotly_chart(fig_demanda, use_container_width=True)
            st.caption("Mostra a evolução dos vínculos ativos por ocupação e região.")

            rais_escolaridade_grafico = rais_visao.assign(
                Superior_Pos=rais_visao["Grau_Instrucao"].map(normalizar_texto).isin(
                    {
                        "ensino superior completo", "mestrado completo", "doutorado completo",
                        "especializacao completa", "pos graduacao completa",
                    }
                )
            ).groupby(["Ano", "Ocupacao_CBO"], as_index=False).agg(
                Vinculos_Superior_Pos=("Vinculos_Ativos", lambda valores: valores[rais_visao.loc[valores.index, "Grau_Instrucao"].map(normalizar_texto).isin({"ensino superior completo", "mestrado completo", "doutorado completo", "especializacao completa", "pos graduacao completa"})].sum()),
                Total_Vinculos=("Vinculos_Ativos", "sum"),
            )
            rais_escolaridade_grafico["Participacao_Superior_Pos_pct"] = (
                rais_escolaridade_grafico["Vinculos_Superior_Pos"]
                / rais_escolaridade_grafico["Total_Vinculos"].replace(0, np.nan)
                * 100
            )
            fig_escolaridade = px.line(
                rais_escolaridade_grafico,
                x="Ano",
                y="Participacao_Superior_Pos_pct",
                color="Ocupacao_CBO",
                markers=True,
                labels={
                    "Ano": "Ano",
                    "Participacao_Superior_Pos_pct": "Superior completo ou pós (%)",
                    "Ocupacao_CBO": "Ocupação (CBO)",
                },
                template="plotly_white",
            )
            fig_escolaridade.update_layout(height=430, yaxis_range=[0, 100])
            st.plotly_chart(fig_escolaridade, use_container_width=True)
            st.caption(
                "Compara a participação de vínculos com ensino superior ou pós por ocupação ao longo do tempo."
            )

            st.download_button(
                "Baixar análise RAIS (CSV)",
                data=rais_agregado.to_csv(index=False).encode("utf-8-sig"),
                file_name="analise_rais_ti.csv",
                mime="text/csv",
            )

    with tab_comparativo:
        st.subheader("Emprego formal e informal em ocupações de tecnologia")
        st.caption(
            "Referência: RAIS 2025 e PNAD Contínua no 4º trimestre de 2025. "
            "A PNAD mostra trabalhadores informais e formais, e a RAIS representa vínculos formais ativos."
        )

        pnad_cod = pd.DataFrame(
            [
                ("2511", "Analistas de sistemas", 51665, 83, 8844.20),
                ("2512", "Desenvolvedores de programas e aplicativos (software)", 42891, 75, 10109.16),
                ("2513", "Desenvolvedores de páginas de internet (web) e multimídia", 4668, 6, 7160.79),
                ("2514", "Programadores de aplicações", 16778, 29, 5385.60),
                ("2519", "Outros desenvolvedores e analistas de software e multimídia", 2929, 4, 3457.06),
                ("2521", "Desenhistas e administradores de bases de dados", 2235, 4, 14199.27),
                ("2522", "Administradores de sistemas", 3654, 5, 4822.56),
                ("2523", "Profissionais em rede de computadores", 530, 1, 3036.00),
                ("2529", "Outros especialistas em bases de dados e redes", 269, 1, 8000.00),
                ("3511", "Técnicos em operações de TI e comunicações", 80644, 139, 3932.10),
                ("3512", "Técnicos em assistência ao usuário de TI e comunicações", 9806, 18, 10049.42),
                ("3513", "Técnicos de redes e sistemas de computadores", 58107, 94, 3525.63),
                ("3514", "Técnicos da web", 14690, 25, 3454.34),
            ],
            columns=[
                "Código COD",
                "Grupo ocupacional PNAD",
                "Informais estimados",
                "Amostra informal",
                "Rendimento informal médio (R$)",
            ],
        )
        pnad_formais = 1197864
        pnad_informais = int(pnad_cod["Informais estimados"].sum())
        pnad_rendimento_informal = 6067.64

        rais_2025 = df.loc[df["Ano"].eq(2025)].copy()
        if rais_2025.empty:
            st.warning(
                "A base RAIS carregada não contém dados de 2025. "
                "Carregue a planilha RAIS 2022-2025 para exibir o comparativo."
            )
        else:
            rais_vinculos = int(rais_2025["Vinculos_Ativos"].sum())
            rais_massa = (
                rais_2025["Remuneracao_Media"] * rais_2025["Vinculos_Ativos"]
            ).sum()
            rais_remuneracao = rais_massa / rais_vinculos if rais_vinculos else 0
            metrica_rais, metrica_pnad_informal, metrica_pnad_formal = st.columns(3)
            metrica_rais.metric(
                "RAIS · vínculos formais ativos",
                f"{rais_vinculos:,.0f}".replace(",", "."),
                help="Vínculos ativos em 31/12/2025 nas ocupações de tecnologia presentes na planilha RAIS.",
            )
            metrica_pnad_informal.metric(
                "PNAD · ocupados informais estimados",
                f"{pnad_informais:,.0f}".replace(",", "."),
                help="Estimativa ponderada somente dos trabalhadores informais nos grupos COD listados.",
            )
            metrica_pnad_formal.metric(
                "PNAD · ocupados formais estimados",
                f"{pnad_formais:,.0f}".replace(",", "."),
                help="Total estimado de ocupados formais nos mesmos grupos COD e período; exibido separadamente da análise de informais.",
            )

            col_rais, col_pnad_informal = st.columns(2)
            col_rais.metric(
                "RAIS · remuneração média ponderada",
                formatar_moeda(rais_remuneracao),
            )
            col_pnad_informal.metric(
                "PNAD · rendimento habitual informal",
                formatar_moeda(pnad_rendimento_informal),
            )

            st.markdown("#### Ocupações PNAD por formalidade")
            st.dataframe(
                pnad_cod,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Informais estimados": st.column_config.NumberColumn(format="%d"),
                    "Amostra informal": st.column_config.NumberColumn(format="%d"),
                    "Rendimento informal médio (R$)": st.column_config.NumberColumn(
                        format="R$ %.2f"
                    ),
                },
            )
            pnad_grafico = pnad_cod.melt(
                id_vars=["Código COD", "Grupo ocupacional PNAD"],
                value_vars=["Informais estimados"],
                var_name="Situação",
                value_name="Pessoas ocupadas estimadas",
            )
            fig_pnad = px.bar(
                pnad_grafico,
                x="Pessoas ocupadas estimadas",
                y="Grupo ocupacional PNAD",
                color="Situação",
                orientation="h",
                hover_data=[
                    "Código COD",
                ],
                labels={
                    "Pessoas ocupadas estimadas": "Pessoas ocupadas (estimativa)",
                    "Grupo ocupacional PNAD": "Grupo ocupacional COD",
                },
                template="plotly_white",
                barmode="group",
            )
            fig_pnad.update_layout(height=600, yaxis_title="", legend_title_text="")
            st.plotly_chart(fig_pnad, use_container_width=True)
            st.caption(
                "A tabela e a análise PNAD mostram somente empregados sem carteira, trabalhadores familiares "
                "auxiliares e empregadores/trabalhadores por conta própria sem CNPJ nos grupos COD "
                "listados. Rendimentos são médias habituais do trabalho principal, ponderadas pelo "
                "peso amostral, entre respostas válidas. Amostras pequenas geram maior incerteza. "
                "O total formal da PNAD é mostrado separadamente. A RAIS conta vínculos formais; "
                "os grupos COD da PNAD não correspondem exatamente "
                "às oito ocupações da planilha RAIS."
            )

            st.markdown(
                "Fontes: [microdados PNAD Contínua — IBGE, 4º trimestre de 2025]"
                "(https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Trimestre/Trimestre_4/Dados/PNADC_2025_trimestre4_20260702.zip) · "
                "[dicionário de variáveis PNAD]"
                "(https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Trimestre/Trimestre_4/Documentacao/dicionario_PNADC_microdados_trimestre4_20260702.xls) · "
                "RAIS: planilha local carregada no aplicativo."
            )

            st.download_button(
                "Baixar comparação PNAD formal e informal (CSV)",
                data=pnad_cod.to_csv(index=False).encode("utf-8-sig"),
                file_name="comparativo_pnad_formal_informal_cod_2025.csv",
                mime="text/csv",
            )

    with tab_tic:
        st.subheader("Adoção de IA e barreira de pessoal qualificado")
        if df_tic_adocao.empty or df_tic_barreiras.empty:
            st.warning("Não foi possível carregar tic_empresas_2021_2025.xlsx.")
        else:
            anos_h13_indisponiveis = sorted(
                set(anos_tic_sel).intersection(anos_h13_sem_resposta_positiva)
            )
            if anos_h13_indisponiveis:
                detalhes_h13 = []
                for ano in anos_h13_indisponiveis:
                    registros_h13_ano = df_tic_microdados.loc[
                        df_tic_microdados["Ano"].eq(ano)
                        & df_tic_microdados["Regiao"].isin(regioes_tic_sel)
                        & df_tic_microdados["Setor_TIC"].isin(setores_tic_sel)
                    ]
                    if porte_tic_sel != "Todos os portes":
                        registros_h13_ano = registros_h13_ano.loc[
                            registros_h13_ano["Porte"].eq(porte_tic_sel)
                        ]
                    distribuicao_h13 = (
                        registros_h13_ano["Barreira_Pessoal_Resposta_Original"]
                        .fillna("Sem resposta")
                        .value_counts()
                    )
                    distribuicao_texto = "; ".join(
                        f"{rotulo}: {quantidade:,}".replace(",", ".")
                        for rotulo, quantidade in distribuicao_h13.items()
                    )
                    detalhes_h13.append(f"{ano}: {distribuicao_texto}")
                st.warning(
                    "Sem estimativa para falta de profissionais qualificados: "
                    + " | ".join(detalhes_h13)
                    + ". Esses rótulos não equivalem a respostas 'Sim' ou 'Não'; "
                    "a ausência de informação não indica que a barreira inexista."
                )
            tic_adocao_visao = df_tic_adocao.loc[
                df_tic_adocao["Ano"].isin(anos_tic_sel)
                & df_tic_adocao["Regiao"].isin(regioes_tic_sel)
                & df_tic_adocao["Setor_TIC"].isin(setores_tic_sel)
                & df_tic_adocao["Porte"].eq(porte_tic_sel)
            ]
            tic_barreira_visao = df_tic_barreiras.loc[
                df_tic_barreiras["Ano"].isin(anos_tic_sel)
                & df_tic_barreiras["Barreira"].map(normalizar_texto).str.contains(
                    "profissionais qualificados", na=False
                )
                & df_tic_barreiras["Regiao"].isin(regioes_tic_sel)
                & df_tic_barreiras["Setor_TIC"].isin(setores_tic_sel)
                & df_tic_barreiras["Porte"].eq(porte_tic_sel)
            ]
            tabela_tic = tic_adocao_visao.merge(
                tic_barreira_visao[
                    ["Ano", "Regiao", "Porte", "Setor_TIC", "Proporcao_pct"]
                ],
                on=["Ano", "Regiao", "Porte", "Setor_TIC"],
                how="left",
            ).rename(columns={"Proporcao_pct": "Barreira_Pessoal_Qualificado_pct"})
            tabela_tic["Nao_Adotou_IA_pct"] = 100 - tabela_tic["Adocao_IA_pct"]
            tabela_tic = tabela_tic[
                [
                    "Ano", "Regiao", "Porte", "Setor_TIC", "Divisoes_CNAE_2_0",
                    "Adocao_IA_pct", "Nao_Adotou_IA_pct", "Barreira_Pessoal_Qualificado_pct",
                ]
            ].sort_values(["Ano", "Regiao", "Setor_TIC"])

            st.markdown("#### Relação entre adoção de IA e falta de pessoal qualificado")
            tabela_relacao = tabela_tic.dropna(
                subset=["Barreira_Pessoal_Qualificado_pct"]
            )
            if tabela_relacao.empty:
                st.info(
                    "Não há anos com respostas válidas para cruzar adoção e falta de pessoal "
                    "nos filtros selecionados."
                )
            else:
                fig_relacao = px.scatter(
                    tabela_relacao,
                    x="Barreira_Pessoal_Qualificado_pct",
                    y="Adocao_IA_pct",
                    color="Setor_TIC",
                    symbol="Regiao",
                    animation_frame="Ano",
                    hover_data=["Porte", "Divisoes_CNAE_2_0"],
                    labels={
                        "Barreira_Pessoal_Qualificado_pct": "Falta de pessoal qualificado (%)",
                        "Adocao_IA_pct": "Adoção de IA (%)",
                        "Setor_TIC": "Setor",
                        "Regiao": "Região",
                        "Ano": "Ano",
                    },
                    template="plotly_white",
                )
                fig_relacao.update_layout(
                    height=560, xaxis_range=[0, 100], yaxis_range=[0, 100]
                )
                fig_relacao.add_annotation(
                    x=0.99,
                    y=0.02,
                    xref="paper",
                    yref="paper",
                    text="2025: sem respostas válidas",
                    showarrow=False,
                    xanchor="right",
                    bgcolor="white",
                    bordercolor="#f59e0b",
                    borderpad=5,
                )
                st.plotly_chart(fig_relacao, use_container_width=True)
                st.caption(
                    "Relaciona a adoção de IA à falta de profissionais qualificados nos recortes disponíveis."
                )

            st.markdown("#### Indicadores por ano e região")
            tic_regiao = df_tic_adocao.loc[
                (df_tic_adocao["Setor_TIC"] == "Todos os setores")
                & df_tic_adocao["Ano"].isin(anos_tic_sel)
                & df_tic_adocao["Regiao"].isin(regioes_tic_sel)
                & df_tic_adocao["Porte"].eq(porte_tic_sel),
                ["Ano", "Regiao", "Porte", "Adocao_IA_pct"],
            ]
            tic_barreira_regiao = df_tic_barreiras.loc[
                (df_tic_barreiras["Setor_TIC"] == "Todos os setores")
                & df_tic_barreiras["Barreira"].map(normalizar_texto).str.contains(
                    "profissionais qualificados", na=False
                )
                & df_tic_barreiras["Ano"].isin(anos_tic_sel)
                & df_tic_barreiras["Regiao"].isin(regioes_tic_sel)
                & df_tic_barreiras["Porte"].eq(porte_tic_sel),
                ["Ano", "Regiao", "Porte", "Proporcao_pct"],
            ].rename(columns={"Proporcao_pct": "Barreira_Pessoal_Qualificado_pct"})
            tic_regiao = tic_regiao.merge(
                tic_barreira_regiao, on=["Ano", "Regiao", "Porte"], how="left"
            )
            graf1, graf2 = st.columns(2)
            with graf1:
                fig_adocao_regiao = px.line(
                    tic_regiao,
                    x="Ano",
                    y="Adocao_IA_pct",
                    color="Regiao",
                    markers=True,
                    labels={"Ano": "Ano", "Adocao_IA_pct": "Adoção de IA (%)", "Regiao": "Região"},
                    template="plotly_white",
                )
                fig_adocao_regiao.update_layout(height=400, yaxis_range=[0, 100])
                st.plotly_chart(fig_adocao_regiao, use_container_width=True)
                st.caption("Compara a adoção de IA entre regiões ao longo dos anos.")
            with graf2:
                fig_barreira_regiao = px.line(
                    tic_regiao,
                    x="Ano",
                    y="Barreira_Pessoal_Qualificado_pct",
                    color="Regiao",
                    markers=True,
                    labels={
                        "Ano": "Ano",
                        "Barreira_Pessoal_Qualificado_pct": "Barreira de pessoal (%)",
                        "Regiao": "Região",
                    },
                    template="plotly_white",
                )
                anos_grafico = sorted(set(anos_tic_sel))
                fig_barreira_regiao.update_layout(
                    height=400,
                    yaxis_range=[0, 100],
                    xaxis=dict(
                        tickmode="array",
                        tickvals=anos_grafico,
                        ticktext=[str(ano) for ano in anos_grafico],
                        range=[min(anos_grafico), max(anos_grafico)]
                        if len(anos_grafico) > 1
                        else None,
                    ),
                )
                st.plotly_chart(fig_barreira_regiao, use_container_width=True)
                st.caption(
                    "Compara entre regiões as respostas sobre falta de profissionais qualificados."
                )

            st.download_button(
                "Baixar análise TIC (CSV)",
                data=tabela_tic.to_csv(index=False).encode("utf-8-sig"),
                file_name="analise_tic_ia_2021_2025.csv",
                mime="text/csv",
            )

            st.markdown("### Novas análises dos microdados · 2021–2025")
            rotulos_tic = df_tic_microdados.attrs.get("rotulos_indicadores", {})
            if df_tic_microdados.empty:
                st.info("Não há microdados disponíveis para as novas análises.")
            else:
                tic_analise = df_tic_microdados.loc[
                    df_tic_microdados["Ano"].isin(anos_tic_sel)
                    & df_tic_microdados["Regiao"].isin(regioes_tic_sel)
                    & df_tic_microdados["Setor_TIC"].isin(setores_tic_sel)
                ].copy()

                def proporcao_ponderada(grupo, indicador):
                    respostas = grupo[indicador].isin([0, 1]) & grupo["Peso"].notna()
                    peso_valido = grupo.loc[respostas, "Peso"].sum()
                    if peso_valido <= 0:
                        return np.nan
                    return (
                        grupo.loc[respostas & grupo[indicador].eq(1), "Peso"].sum()
                        / peso_valido
                        * 100
                    )

                def taxas_agrupadas(dados, chaves, indicador):
                    linhas = []
                    if dados.empty:
                        return pd.DataFrame()
                    for valores, grupo in dados.groupby(chaves, dropna=False, sort=False):
                        valores = valores if isinstance(valores, tuple) else (valores,)
                        linha = dict(zip(chaves, valores))
                        linha["Percentual"] = proporcao_ponderada(grupo, indicador)
                        linha["Respostas_validas"] = int(
                            grupo[indicador].isin([0, 1]).sum()
                        )
                        linhas.append(linha)
                    return pd.DataFrame(linhas)

                def taxas_indicadores(dados, colunas, chaves, dimensao):
                    linhas = []
                    for coluna in colunas:
                        if coluna not in dados.columns:
                            continue
                        serie = taxas_agrupadas(dados, chaves, coluna)
                        if serie.empty:
                            continue
                        serie[dimensao] = rotulos_tic.get(coluna, coluna)
                        linhas.append(serie)
                    return pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame()

                if tic_analise.empty:
                    st.info("Os filtros selecionados não correspondem a registros TIC.")
                else:
                    h8 = [c for c in rotulos_tic if c.startswith("H8_")]
                    h9 = [c for c in rotulos_tic if c.startswith("H9_")]
                    h10 = [c for c in rotulos_tic if c.startswith("H10_")]
                    h13 = [c for c in rotulos_tic if c.startswith("H13_")]
                    campo_pessoal = next(
                        (
                            coluna
                            for coluna in h13
                            if "profissionais qualificados"
                            in normalizar_texto(rotulos_tic.get(coluna, ""))
                        ),
                        None,
                    )
                    anos_indicadores = sorted(tic_analise["Ano"].unique())
                    ano_recente = int(anos_indicadores[-1])
                    tic_nao_adotantes = tic_analise.loc[
                        tic_analise["Adotou_IA"].eq(0)
                    ].copy()
                    barreiras_pessoais_selecionadas = df_tic_barreiras.loc[
                        df_tic_barreiras["Ano"].isin(anos_tic_sel)
                        & df_tic_barreiras["Regiao"].isin(regioes_tic_sel)
                        & df_tic_barreiras["Setor_TIC"].isin(setores_tic_sel)
                        & df_tic_barreiras["Barreira"].map(normalizar_texto).str.contains(
                            "profissionais qualificados", na=False
                        )
                    ]
                    anos_barreiras_validas = sorted(
                        int(ano)
                        for ano, grupo in tic_nao_adotantes.groupby("Ano")
                        if any(
                            grupo[coluna].isin([0, 1]).any()
                            for coluna in h13
                            if coluna in grupo
                        )
                    )
                    anos_barreiras_validas = sorted(
                        set(anos_barreiras_validas)
                        | set(
                            int(ano)
                            for ano in barreiras_pessoais_selecionadas["Ano"].unique()
                        )
                    )
                    ano_barreira_recente = (
                        anos_barreiras_validas[-1] if anos_barreiras_validas else None
                    )

                    st.markdown("#### Adoção de IA e crescimento anual")
                    adocao_tempo = taxas_agrupadas(
                        tic_analise, ["Ano"], "Adotou_IA"
                    ).sort_values("Ano")
                    if not adocao_tempo.empty:
                        adocao_tempo["Variacao_pp"] = adocao_tempo["Percentual"].diff()
                        fig_adocao_tempo = px.line(
                            adocao_tempo,
                            x="Ano",
                            y="Percentual",
                            markers=True,
                            hover_data=["Respostas_validas", "Variacao_pp"],
                            labels={
                                "Ano": "Ano da pesquisa",
                                "Percentual": "Empresas que adotaram IA (%)",
                                "Respostas_validas": "Respostas válidas",
                                "Variacao_pp": "Variação anual (p.p.)",
                            },
                            template="plotly_white",
                        )
                        fig_adocao_tempo.update_layout(height=390, yaxis_range=[0, 100])
                        st.plotly_chart(fig_adocao_tempo, use_container_width=True)
                        st.caption(
                            "Mostra a proporção de empresas que adotaram IA em cada ano."
                        )

                    graf_tipos, graf_barreiras = st.columns(2)
                    with graf_tipos:
                        st.markdown("#### Tecnologias de IA por ano")
                        tipos_tempo = taxas_indicadores(
                            tic_analise, h9, ["Ano"], "Tecnologia"
                        )
                        if not tipos_tempo.empty:
                            fig_tipos_tempo = px.line(
                                tipos_tempo,
                                x="Ano",
                                y="Percentual",
                                color="Tecnologia",
                                markers=True,
                                labels={
                                    "Ano": "Ano",
                                    "Percentual": "Percentual entre respostas válidas (%)",
                                },
                                template="plotly_white",
                            )
                            anos_tecnologias_exibidos = sorted(
                                int(ano) for ano in tipos_tempo["Ano"].unique()
                            )
                            fig_tipos_tempo.update_layout(
                                height=600,
                                margin=dict(b=190),
                                yaxis=dict(rangemode="tozero"),
                                xaxis=dict(
                                    tickmode="array",
                                    tickvals=anos_tecnologias_exibidos,
                                    ticktext=[
                                        str(ano) for ano in anos_tecnologias_exibidos
                                    ],
                                    tickangle=0,
                                ),
                                legend=dict(
                                    orientation="v",
                                    x=0.5,
                                    y=-0.25,
                                    xanchor="center",
                                    yanchor="top",
                                    font=dict(size=10),
                                ),
                            )
                            st.plotly_chart(fig_tipos_tempo, use_container_width=True)
                            st.caption(
                                "Compara a proporção de respostas válidas para cada tecnologia de IA por ano."
                            )
                    with graf_barreiras:
                        st.markdown("#### Barreiras declaradas ao longo do tempo")
                        barreiras_tempo = taxas_indicadores(
                            tic_nao_adotantes, h13, ["Ano"], "Barreira"
                        )
                        barreiras_pessoais_tempo = (
                            barreiras_pessoais_selecionadas.loc[
                                barreiras_pessoais_selecionadas["Ano"].eq(2025)
                                & barreiras_pessoais_selecionadas["Porte"].eq(
                                    "Todos os portes"
                                )
                            ]
                            .groupby("Ano", as_index=False)
                            .agg(
                                Peso_Respostas_Validas=(
                                    "Peso_Respostas_Validas",
                                    "sum",
                                ),
                                Peso_Respostas_Sim=(
                                    "Empresas_Indicaram_Estimadas",
                                    "sum",
                                ),
                                Respostas_validas=("Respostas_Validas", "sum"),
                            )
                        )
                        if not barreiras_pessoais_tempo.empty:
                            barreiras_pessoais_tempo["Percentual"] = (
                                barreiras_pessoais_tempo["Peso_Respostas_Sim"]
                                / barreiras_pessoais_tempo[
                                    "Peso_Respostas_Validas"
                                ]
                                * 100
                            )
                            barreiras_pessoais_tempo["Barreira"] = (
                                rotulos_tic.get(
                                    campo_pessoal,
                                    "Falta de profissionais qualificados",
                                )
                            )
                            barreiras_tempo = pd.concat(
                                [
                                    barreiras_tempo,
                                    barreiras_pessoais_tempo[
                                        [
                                            "Ano",
                                            "Percentual",
                                            "Respostas_validas",
                                            "Barreira",
                                        ]
                                    ],
                                ],
                                ignore_index=True,
                            )
                        if not barreiras_tempo.empty:
                            fig_barreiras_tempo = px.line(
                                barreiras_tempo,
                                x="Ano",
                                y="Percentual",
                                color="Barreira",
                                markers=True,
                                labels={
                                    "Ano": "Ano",
                                    "Percentual": "Entre respostas válidas (%)",
                                },
                                template="plotly_white",
                            )
                            anos_barreiras_exibidos = sorted(
                                int(ano) for ano in tic_analise["Ano"].unique()
                            )
                            fig_barreiras_tempo.update_layout(
                                height=600,
                                margin=dict(b=190),
                                yaxis=dict(rangemode="tozero"),
                                xaxis=dict(
                                    tickmode="array",
                                    tickvals=anos_barreiras_exibidos,
                                    ticktext=[
                                        str(ano) for ano in anos_barreiras_exibidos
                                    ],
                                    tickangle=0,
                                    range=[
                                        min(anos_barreiras_exibidos),
                                        max(anos_barreiras_exibidos),
                                    ]
                                    if len(anos_barreiras_exibidos) > 1
                                    else None,
                                ),
                                legend=dict(
                                    orientation="v",
                                    x=0.5,
                                    y=-0.25,
                                    xanchor="center",
                                    yanchor="top",
                                    font=dict(size=10),
                                ),
                            )
                            if (
                                anos_barreiras_exibidos
                                and max(anos_barreiras_exibidos)
                                not in anos_barreiras_validas
                            ):
                                sem_respostas_barreiras_ano = max(
                                    anos_barreiras_exibidos
                                )
                            else:
                                sem_respostas_barreiras_ano = None
                            st.plotly_chart(fig_barreiras_tempo, use_container_width=True)
                            st.caption(
                                "Compara as barreiras informadas por empresas que não adotaram IA ao longo dos anos."
                            )
                            if sem_respostas_barreiras_ano is not None:
                                st.caption(
                                    "Sem respostas válidas para barreiras em "
                                    f"{sem_respostas_barreiras_ano}."
                                )

                    st.markdown("#### Adoção por perfil empresarial · porte e região")
                    por_porte, por_regiao = st.columns(2)
                    with por_porte:
                        adocao_porte = taxas_agrupadas(
                            tic_analise, ["Ano", "Porte"], "Adotou_IA"
                        )
                        if not adocao_porte.empty:
                            fig_porte = px.line(
                                adocao_porte,
                                x="Ano",
                                y="Percentual",
                                color="Porte",
                                markers=True,
                                labels={
                                    "Ano": "Ano",
                                    "Percentual": "Adoção de IA (%)",
                                    "Porte": "Porte da empresa",
                                },
                                template="plotly_white",
                            )
                            fig_porte.update_layout(height=410, yaxis_range=[0, 100])
                            st.plotly_chart(fig_porte, use_container_width=True)
                            st.caption("Compara a adoção de IA entre portes de empresa ao longo dos anos.")
                    with por_regiao:
                        adocao_regiao = taxas_agrupadas(
                            tic_analise, ["Ano", "Regiao"], "Adotou_IA"
                        )
                        if not adocao_regiao.empty:
                            fig_regiao = px.line(
                                adocao_regiao,
                                x="Ano",
                                y="Percentual",
                                color="Regiao",
                                markers=True,
                                labels={
                                    "Ano": "Ano",
                                    "Percentual": "Adoção de IA (%)",
                                    "Regiao": "Região",
                                },
                                template="plotly_white",
                            )
                            fig_regiao.update_layout(height=410, yaxis_range=[0, 100])
                            st.plotly_chart(fig_regiao, use_container_width=True)
                            st.caption("Compara a adoção de IA entre regiões ao longo dos anos.")
                    tipos_por_porte = taxas_indicadores(
                        tic_analise.loc[tic_analise["Ano"].eq(ano_recente)],
                        h9,
                        ["Porte"],
                        "Tecnologia",
                    )
                    if not tipos_por_porte.empty:
                        st.markdown(
                            f"#### Tecnologias de IA por porte · {ano_recente}"
                        )
                        fig_tipos_porte = px.bar(
                            tipos_por_porte,
                            x="Tecnologia",
                            y="Percentual",
                            color="Porte",
                            barmode="group",
                            labels={
                                "Percentual": "Entre respostas válidas (%)",
                                "Tecnologia": "Tipo de IA",
                                "Porte": "Porte da empresa",
                            },
                            template="plotly_white",
                        )
                        fig_tipos_porte.update_layout(
                            height=500, yaxis_range=[0, 100]
                        )
                        st.plotly_chart(fig_tipos_porte, use_container_width=True)
                        st.caption(
                            f"Compara as tecnologias de IA declaradas por porte de empresa em {ano_recente}."
                        )

                    st.markdown("#### Capacidade interna e estratégias de aquisição")
                    habilitadores = []
                    nomes_habilitadores = {
                        "Especialista_TI": "Especialista interno em TI",
                        "Big_Data": "Uso de Big Data",
                        "Analise_Avancada": "Análise avançada de dados",
                    }
                    for indicador, nome in nomes_habilitadores.items():
                        if indicador not in tic_analise:
                            continue
                        comparacao = taxas_agrupadas(
                            tic_analise.loc[
                                tic_analise["Ano"].eq(ano_recente)
                                & tic_analise[indicador].notna()
                            ],
                            [indicador],
                            "Adotou_IA",
                        )
                        if not comparacao.empty:
                            comparacao["Habilitador"] = nome
                            comparacao["Perfil"] = comparacao[indicador].map(
                                {1.0: "Sim", 0.0: "Não"}
                            )
                            habilitadores.append(comparacao)
                    if habilitadores:
                        comparacao_habilitadores = pd.concat(
                            habilitadores, ignore_index=True
                        )
                        fig_habilitadores = px.bar(
                            comparacao_habilitadores,
                            x="Habilitador",
                            y="Percentual",
                            color="Perfil",
                            barmode="group",
                            labels={
                                "Percentual": "Adoção de IA (%)",
                                "Perfil": "Resposta",
                            },
                            template="plotly_white",
                        )
                        fig_habilitadores.update_layout(height=430, yaxis_range=[0, 100])
                        st.plotly_chart(fig_habilitadores, use_container_width=True)
                        st.caption(
                            "Compara a adoção de IA conforme a empresa declara possuir cada capacidade interna."
                        )

                    formas_aquisicao = taxas_indicadores(
                        tic_analise, h8, ["Ano"], "Forma de aquisição"
                    )
                    if not formas_aquisicao.empty:
                        st.markdown("#### Comprar, customizar ou desenvolver")
                        fig_aquisicao = px.line(
                            formas_aquisicao,
                            x="Ano",
                            y="Percentual",
                            color="Forma de aquisição",
                            markers=True,
                            labels={
                                "Ano": "Ano",
                                "Percentual": "Entre respostas válidas (%)",
                            },
                            template="plotly_white",
                        )
                        fig_aquisicao.update_layout(height=440, yaxis_range=[0, 100])
                        st.plotly_chart(fig_aquisicao, use_container_width=True)
                        st.caption(
                            "Mostra como as empresas obtêm soluções de IA em cada ano."
                        )

                    st.markdown("#### Áreas de aplicação de IA por setor")
                    aplicacoes_setor = taxas_indicadores(
                        tic_analise.loc[tic_analise["Ano"].eq(ano_recente)],
                        h10,
                        ["Setor_TIC"],
                        "Área organizacional",
                    )
                    if not aplicacoes_setor.empty:
                        matriz_aplicacao = aplicacoes_setor.pivot(
                            index="Setor_TIC",
                            columns="Área organizacional",
                            values="Percentual",
                        )
                        fig_aplicacoes_setor = px.imshow(
                            matriz_aplicacao,
                            aspect="auto",
                            text_auto=".1f",
                            color_continuous_scale="Teal",
                            labels={
                                "x": "Área organizacional",
                                "y": "Setor econômico",
                                "color": "Empresas (%)",
                            },
                        )
                        fig_aplicacoes_setor.update_layout(
                            height=max(420, 55 * len(matriz_aplicacao))
                        )
                        st.plotly_chart(fig_aplicacoes_setor, use_container_width=True)
                        st.caption(
                            "Mostra em quais áreas organizacionais cada setor aplica IA."
                        )

                    campo_pessoal = next(
                        (
                            coluna
                            for coluna in h13
                            if "profissionais qualificados"
                            in normalizar_texto(rotulos_tic.get(coluna, ""))
                        ),
                        None,
                    )
                    barreira_pessoal_perfil = pd.DataFrame()
                    if campo_pessoal and ano_barreira_recente is not None:
                        st.markdown(
                            "#### Qualificação em TI e barreira de pessoal · "
                            f"{ano_barreira_recente}"
                        )
                        if ano_barreira_recente == 2025:
                            barreira_pessoal_perfil = (
                                barreiras_pessoais_selecionadas.loc[
                                    barreiras_pessoais_selecionadas["Ano"].eq(2025)
                                    & barreiras_pessoais_selecionadas["Porte"].ne(
                                        "Todos os portes"
                                    )
                                    & barreiras_pessoais_selecionadas["Setor_TIC"].ne(
                                        "Todos os setores"
                                    )
                                ]
                                .groupby(["Regiao", "Porte"], as_index=False)
                                .agg(
                                    Peso_Respostas_Validas=(
                                        "Peso_Respostas_Validas",
                                        "sum",
                                    ),
                                    Peso_Respostas_Sim=(
                                        "Empresas_Indicaram_Estimadas",
                                        "sum",
                                    ),
                                    Respostas_validas=("Respostas_Validas", "sum"),
                                )
                            )
                            if not barreira_pessoal_perfil.empty:
                                barreira_pessoal_perfil["Percentual"] = (
                                    barreira_pessoal_perfil["Peso_Respostas_Sim"]
                                    / barreira_pessoal_perfil[
                                        "Peso_Respostas_Validas"
                                    ]
                                    * 100
                                )
                                barreira_pessoal_perfil["Barreira"] = (
                                    rotulos_tic.get(
                                        campo_pessoal,
                                        "Falta de profissionais qualificados",
                                    )
                                )
                            dificuldade_pessoal = barreira_pessoal_perfil
                        else:
                            dificuldade_pessoal = taxas_agrupadas(
                                tic_nao_adotantes.loc[
                                    tic_nao_adotantes["Ano"].eq(
                                        ano_barreira_recente
                                    )
                                ],
                                ["Regiao", "Porte"],
                                campo_pessoal,
                            )
                        if not dificuldade_pessoal.empty:
                            fig_dificuldade = px.bar(
                                dificuldade_pessoal,
                                x="Regiao",
                                y="Percentual",
                                color="Porte",
                                barmode="group",
                                labels={
                                    "Regiao": "Região",
                                    "Percentual": "Empresas que indicaram a barreira (%)",
                                    "Porte": "Porte",
                                },
                                template="plotly_white",
                            )
                            fig_dificuldade.update_layout(height=430, yaxis_range=[0, 100])
                            st.plotly_chart(fig_dificuldade, use_container_width=True)
                            st.caption(
                                f"Compara essa barreira por região e porte em {ano_barreira_recente}."
                            )
                    else:
                        st.info(
                            "Não há respostas válidas sobre falta de profissionais "
                            "qualificados nos anos e filtros selecionados."
                        )
                    if ano_barreira_recente is not None:
                        barreiras_perfil = taxas_indicadores(
                            tic_nao_adotantes.loc[
                                tic_nao_adotantes["Ano"].eq(ano_barreira_recente)
                            ],
                            h13,
                            ["Regiao", "Porte"],
                            "Barreira",
                        )
                        if not barreira_pessoal_perfil.empty:
                            rotulo_barreira_pessoal = rotulos_tic.get(
                                campo_pessoal,
                                "Falta de profissionais qualificados",
                            )
                            barreiras_perfil = barreiras_perfil.loc[
                                barreiras_perfil["Barreira"].ne(
                                    rotulo_barreira_pessoal
                                )
                            ]
                            barreiras_perfil = pd.concat(
                                [barreiras_perfil, barreira_pessoal_perfil],
                                ignore_index=True,
                            )
                        barreiras_perfil = barreiras_perfil.dropna(
                            subset=["Percentual"]
                        )
                        if not barreiras_perfil.empty:
                            barreiras_perfil["Regiao · porte"] = (
                                barreiras_perfil["Regiao"]
                                + " · "
                                + barreiras_perfil["Porte"]
                            )
                            matriz_barreiras = barreiras_perfil.pivot(
                                index="Barreira",
                                columns="Regiao · porte",
                                values="Percentual",
                            )
                            st.markdown(
                                "#### Perfil regional das barreiras por porte · "
                                f"{ano_barreira_recente}"
                            )
                            fig_matriz_barreiras = px.imshow(
                                matriz_barreiras,
                                aspect="auto",
                                text_auto=".1f",
                                color_continuous_scale="Oranges",
                                labels={
                                    "x": "Região e porte",
                                    "y": "Barreira declarada",
                                    "color": "Empresas (%)",
                                },
                            )
                            fig_matriz_barreiras.update_layout(
                                height=max(440, 52 * len(matriz_barreiras))
                            )
                            st.plotly_chart(
                                fig_matriz_barreiras, use_container_width=True
                            )
                            st.caption(
                                "Compara a frequência das barreiras por combinação de região e porte."
                            )

    with tab_cursos:
        if df_tic_adocao.empty:
            st.info("A análise de cursos depende da planilha TIC Empresas disponível no projeto.")
        elif not anos_tic_sel or not regioes_tic_sel or not setores_tic_sel:
            st.info("Selecione ao menos um ano, uma região e um setor nos filtros TIC Empresas.")
        else:
            cursos_adocao = df_tic_adocao.loc[
                df_tic_adocao["Ano"].isin(anos_tic_sel)
                & df_tic_adocao["Regiao"].isin(regioes_tic_sel)
                & df_tic_adocao["Setor_TIC"].isin(setores_tic_sel)
                & df_tic_adocao["Porte"].eq(porte_tic_sel)
            ].copy()
            cursos_barreiras = df_tic_barreiras.loc[
                df_tic_barreiras["Ano"].isin(anos_tic_sel)
                & df_tic_barreiras["Barreira"].map(normalizar_texto).str.contains(
                    "profissionais qualificados", na=False
                )
                & df_tic_barreiras["Regiao"].isin(regioes_tic_sel)
                & df_tic_barreiras["Setor_TIC"].isin(setores_tic_sel)
                & df_tic_barreiras["Porte"].eq(porte_tic_sel)
            ]
            cursos_sinais = cursos_adocao.merge(
                cursos_barreiras[
                    [
                        "Ano",
                        "Regiao",
                        "Porte",
                        "Setor_TIC",
                        "Proporcao_pct",
                        "Peso_Respostas_Validas",
                        "Respostas_Validas",
                        "Empresas_Indicaram_Estimadas",
                    ]
                ].rename(columns={"Proporcao_pct": "Falta_Pessoal_Qualificado_pct"}),
                on=["Ano", "Regiao", "Porte", "Setor_TIC"],
                how="left",
            )

            if cursos_sinais.empty:
                st.info(
                    "Não há registros para os filtros selecionados."
                )
            else:
                ano_referencia = int(cursos_sinais["Ano"].max())
                sinais_atuais = cursos_sinais.loc[
                    cursos_sinais["Ano"].eq(ano_referencia)
                ].copy()
                respostas_adocao_sinal = cursos_adocao.loc[
                    cursos_adocao["Ano"].eq(ano_referencia)
                ]
                peso_adocao_sinal = respostas_adocao_sinal[
                    "Peso_Adocao_Valido"
                ].sum()
                percentual_adocao_sinal = (
                    respostas_adocao_sinal["Empresas_Adotantes_Estimadas"].sum()
                    / peso_adocao_sinal
                    * 100
                    if peso_adocao_sinal > 0
                    else None
                )
                respostas_adocao_validas = int(
                    respostas_adocao_sinal["Respostas_Adocao_Validas"].sum()
                )
                barreiras_com_amostra = cursos_sinais.loc[
                    cursos_sinais["Falta_Pessoal_Qualificado_pct"].notna()
                    & cursos_sinais["Respostas_Validas"].ge(30)
                ]
                ano_barreira_cursos = (
                    int(barreiras_com_amostra["Ano"].max())
                    if not barreiras_com_amostra.empty
                    else None
                )
                respostas_barreira_recentes = (
                    cursos_sinais.loc[
                        cursos_sinais["Ano"].eq(ano_barreira_cursos)
                        & cursos_sinais["Falta_Pessoal_Qualificado_pct"].notna()
                    ]
                    if ano_barreira_cursos is not None
                    else cursos_sinais.iloc[0:0]
                )
                peso_barreira = respostas_barreira_recentes[
                    "Peso_Respostas_Validas"
                ].sum()
                percentual_barreira = (
                    respostas_barreira_recentes[
                        "Empresas_Indicaram_Estimadas"
                    ].sum()
                    / peso_barreira
                    * 100
                    if peso_barreira > 0
                    else None
                )
                respostas_barreira_validas = int(
                    respostas_barreira_recentes["Respostas_Validas"].sum()
                )
                minimo_respostas_sinal = 30

                metrica_adocao, metrica_pessoal, metrica_recorte = st.columns(3)
                if respostas_adocao_validas >= minimo_respostas_sinal:
                    metrica_adocao.metric(
                        f"Adoção ponderada · {ano_referencia}",
                        f"{percentual_adocao_sinal:.1f}%",
                        (
                            f"{respostas_adocao_validas:,} resposta válida"
                            if respostas_adocao_validas == 1
                            else f"{respostas_adocao_validas:,} respostas válidas"
                        ),
                        help=(
                            "Percentual ponderado agregado para as regiões e setores "
                            "selecionados. Anos com escala de peso inválida são excluídos."
                        ),
                    )
                else:
                    metrica_adocao.metric(
                        f"Adoção ponderada · {ano_referencia}",
                        "Base pequena",
                        (
                            f"{respostas_adocao_validas:,} resposta; mínimo 30"
                            if respostas_adocao_validas == 1
                            else f"{respostas_adocao_validas:,} respostas; mínimo 30"
                        ),
                        help="O percentual não é exibido com menos de 30 respostas válidas.",
                    )
                if (
                    ano_barreira_cursos is not None
                    and respostas_barreira_validas >= minimo_respostas_sinal
                    and peso_barreira > 0
                ):
                    metrica_pessoal.metric(
                        f"Falta de pessoal · {ano_barreira_cursos}",
                        f"{percentual_barreira:.1f}%",
                        (
                            f"{respostas_barreira_validas:,} resposta válida"
                            if respostas_barreira_validas == 1
                            else f"{respostas_barreira_validas:,} respostas válidas"
                        ),
                        help=(
                            "Percentual ponderado agregado entre empresas não adotantes "
                            "com resposta válida nas regiões e setores selecionados."
                        ),
                    )
                else:
                    metrica_pessoal.metric(
                        "Falta de pessoal",
                        "Base pequena"
                        if ano_barreira_cursos is not None
                        else "Sem estimativa",
                        (
                            (
                                f"{respostas_barreira_validas:,} resposta; mínimo 30"
                                if respostas_barreira_validas == 1
                                else f"{respostas_barreira_validas:,} respostas; mínimo 30"
                            )
                            if ano_barreira_cursos is not None
                            else "Sem respostas válidas no recorte"
                        ),
                        help="O percentual não é exibido com menos de 30 respostas válidas.",
                    )
                metrica_recorte.metric(
                    "Ano mais recente no recorte",
                    str(ano_referencia),
                    f"{sinais_atuais['Setor_TIC'].nunique()} setores · "
                    f"{sinais_atuais['Regiao'].nunique()} regiões",
                )

                sinais_barreira_recente = (
                    cursos_sinais.loc[
                        cursos_sinais["Ano"].eq(ano_barreira_cursos)
                        & cursos_sinais["Falta_Pessoal_Qualificado_pct"].notna()
                        & cursos_sinais["Respostas_Validas"].ge(
                            minimo_respostas_sinal
                        )
                    ].copy()
                    if ano_barreira_cursos is not None
                    else cursos_sinais.iloc[0:0].copy()
                )
                st.markdown("#### Onde adoção e capacitação se encontram")
                if not sinais_barreira_recente.empty:
                    fig_oportunidades = px.scatter(
                        sinais_barreira_recente,
                        x="Falta_Pessoal_Qualificado_pct",
                        y="Adocao_IA_pct",
                        color="Setor_TIC",
                        symbol="Regiao",
                        hover_data=[
                            "Porte",
                            "Divisoes_CNAE_2_0",
                            "Respostas_Validas",
                        ],
                        labels={
                            "Falta_Pessoal_Qualificado_pct": "Falta de pessoal qualificado (%)",
                            "Adocao_IA_pct": "Adoção de IA (%)",
                            "Setor_TIC": "Setor",
                            "Regiao": "Região",
                        },
                        template="plotly_white",
                    )
                    pontos_com_barreira = sinais_barreira_recente
                    fig_oportunidades.add_hline(
                        y=pontos_com_barreira["Adocao_IA_pct"].median(),
                        line_dash="dot",
                        line_color="#94a3b8",
                    )
                    fig_oportunidades.add_vline(
                        x=pontos_com_barreira["Falta_Pessoal_Qualificado_pct"].median(),
                        line_dash="dot",
                        line_color="#94a3b8",
                    )
                    fig_oportunidades.update_layout(
                        height=470, xaxis_range=[0, 100], yaxis_range=[0, 100]
                    )
                    st.plotly_chart(fig_oportunidades, use_container_width=True)
                    st.caption(
                        "Relaciona adoção de IA e falta de profissionais qualificados por setor e região."
                    )
                else:
                    st.info(
                        "A barreira de pessoal não pôde ser estimada para os filtros "
                        "selecionados; veja as ressalvas da aba TIC Empresas."
                    )

                anos_comparaveis = sorted(cursos_sinais["Ano"].unique())
                if len(anos_comparaveis) >= 2:
                    ano_inicio = int(anos_comparaveis[0])
                    inicio = cursos_sinais.loc[
                        cursos_sinais["Ano"].eq(ano_inicio),
                        ["Regiao", "Porte", "Setor_TIC", "Adocao_IA_pct"],
                    ].rename(columns={"Adocao_IA_pct": "Adocao_Inicial_pct"})
                    fim = cursos_sinais.loc[
                        cursos_sinais["Ano"].eq(ano_referencia),
                        ["Regiao", "Porte", "Setor_TIC", "Adocao_IA_pct"],
                    ].rename(columns={"Adocao_IA_pct": "Adocao_Final_pct"})
                    evolucao_cursos = inicio.merge(
                        fim, on=["Regiao", "Porte", "Setor_TIC"], how="inner"
                    )
                    evolucao_cursos["Variacao_Adocao_pp"] = (
                        evolucao_cursos["Adocao_Final_pct"]
                        - evolucao_cursos["Adocao_Inicial_pct"]
                    )
                    evolucao_cursos = evolucao_cursos.sort_values(
                        "Variacao_Adocao_pp", ascending=False
                    )
                    st.markdown(
                        f"#### Mudança de adoção entre {ano_inicio} e {ano_referencia}"
                    )
                    if evolucao_cursos.empty:
                        st.info("Não há recortes comparáveis entre o primeiro e o último ano.")
                    else:
                        fig_evolucao_cursos = px.bar(
                            evolucao_cursos,
                            x="Variacao_Adocao_pp",
                            y="Setor_TIC",
                            color="Regiao",
                            barmode="group",
                            orientation="h",
                            labels={
                                "Variacao_Adocao_pp": "Variação da adoção (p.p.)",
                                "Setor_TIC": "Setor TIC",
                                "Regiao": "Região",
                            },
                            template="plotly_white",
                        )
                        fig_evolucao_cursos.update_layout(height=460)
                        st.plotly_chart(fig_evolucao_cursos, use_container_width=True)
                        st.caption(
                            "Mostra quanto a adoção de IA mudou, em pontos percentuais, entre os dois anos."
                        )

                st.markdown("#### Trilhas sugeridas pelo briefing")
                cursos_colunas = st.columns(3)
                trilhas = [
                    (
                        "01 · Prioridade de validação",
                        "IA prática para equipes",
                        "Fundamentos, seleção de ferramentas, prompts, validação de respostas "
                        "e rotinas de trabalho.",
                        "Conecta-se à barreira de falta de pessoal qualificado quando há "
                        "estimativa válida no recorte.",
                    ),
                    (
                        "02 · Piloto aplicado",
                        "Automação e IA em processos",
                        "Mapeamento de tarefas, automação de fluxos, integração de ferramentas "
                        "e mensuração de ganhos.",
                        "O briefing recomenda automação e aplicações de negócio; validar casos "
                        "de uso com empresas antes de abrir turmas.",
                    ),
                    (
                        "03 · Trilha complementar",
                        "Dados, governança e uso responsável",
                        "Qualidade de dados, privacidade, supervisão humana e critérios para "
                        "adoção segura.",
                        "Temas estratégicos do briefing que exigem coleta complementar para "
                        "dimensionar a demanda.",
                    ),
                ]
                for coluna, (prioridade, titulo, descricao, evidencias) in zip(
                    cursos_colunas, trilhas
                ):
                    with coluna:
                        st.markdown(
                            f"""
                            <article style="height:100%;background:#fff;border:1px solid #e2e8f0;
                            border-radius:16px;padding:20px;box-shadow:0 5px 18px
                            rgba(15,35,60,.05)">
                                <div style="color:#0f766e;font-size:11px;font-weight:800;
                                letter-spacing:.07em;text-transform:uppercase">{prioridade}</div>
                                <h3 style="font-size:18px;margin:10px 0">{titulo}</h3>
                                <p style="color:#475569;font-size:13px">{descricao}</p>
                                <p style="background:#f8fafc;border:1px solid #e2e8f0;
                                border-radius:10px;padding:11px;color:#334155;font-size:12px">
                                <strong>Evidência/ação:</strong> {evidencias}</p>
                            </article>
                            """,
                            unsafe_allow_html=True,
                        )

                st.download_button(
                    "Baixar sinais e variação para cursos (CSV)",
                    data=cursos_sinais.to_csv(index=False).encode("utf-8-sig"),
                    file_name="sinais_cursos_2027_tic.csv",
                    mime="text/csv",
                )

    st.stop()

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtros Globais")

    anos_disponiveis = sorted(df["Ano"].dropna().unique().tolist())
    anos_selecionados = st.sidebar.multiselect(
        "Selecione os Anos",
        options=anos_disponiveis,
        default=anos_disponiveis,
    )

    cbos_disponiveis = sorted(df["Ocupacao_CBO"].dropna().unique().tolist())
    cbos_selecionados = st.sidebar.multiselect(
        "Selecione as Ocupações (CBO)",
        options=cbos_disponiveis,
        default=cbos_disponiveis,
    )

    df_filtrado = df[
        df["Ano"].isin(anos_selecionados) & df["Ocupacao_CBO"].isin(cbos_selecionados)
    ]
    df_rais_agregado = agregar_rais(df_filtrado)
    df_tic_adocao, df_tic_barreiras, _, df_tic_microdados = carregar_tic_empresas(
        str(diretorio_app), versao_tic
    )

    col1, col2, col3, col4 = st.columns(4)
    total_vinculos = int(df_filtrado["Vinculos_Ativos"].sum())
    massa_salarial = (df_filtrado["Remuneracao_Media"] * df_filtrado["Vinculos_Ativos"]).sum()
    media_remun = float(massa_salarial / total_vinculos) if total_vinculos else 0.0
    total_ocupacoes = df_filtrado["Ocupacao_CBO"].nunique()
    total_setores = df_filtrado["Setor_CNAE"].nunique()

    def formatar_moeda(valor: float) -> str:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    col1.metric("Total de Vínculos Formais", f"{total_vinculos:,.0f}".replace(",", "."))
    col2.metric("Remuneração Média Real", formatar_moeda(media_remun))
    col3.metric("Ocupações Analisadas", f"{total_ocupacoes}")
    col4.metric("Setores (CNAE)", f"{total_setores}")

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📈 Evolução de Vínculos",
            "💰 Evolução Salarial",
            "🏢 Setores (CNAE)",
            "👥 Perfil Demográfico",
            "🧾 RAIS por CNAE",
            "🤖 TIC Empresas (IA)",
        ]
    )

    with tab1:
        st.subheader("Evolução dos Vínculos Formais por Ocupação")
        df_vinculos_ano = (
            df_filtrado.groupby(["Ano", "Ocupacao_CBO"], as_index=False)["Vinculos_Ativos"].sum()
            .rename(columns={"Vinculos_Ativos": "Qtd_Vinculos"})
        )
        fig_vinculos = px.line(
            df_vinculos_ano,
            x="Ano",
            y="Qtd_Vinculos",
            color="Ocupacao_CBO",
            markers=True,
            labels={
                "Qtd_Vinculos": "Total de Vínculos Formais",
                "Ano": "Ano",
                "Ocupacao_CBO": "Ocupação (CBO)",
            },
            template="plotly_white",
        )
        fig_vinculos.update_layout(
            height=500,
            legend_title_text="Ocupação (CBO)",
            legend=dict(x=0.5, y=-0.25, xanchor="center", yanchor="top", orientation="h"),
        )
        st.plotly_chart(fig_vinculos, use_container_width=True)

    with tab2:
        st.subheader("Evolução da Remuneração Média Real por Ocupação")
        df_remun_ano = df_filtrado.assign(
            Massa_Salarial=df_filtrado["Remuneracao_Media"] * df_filtrado["Vinculos_Ativos"]
        ).groupby(["Ano", "Ocupacao_CBO"], as_index=False).agg(
            Massa_Salarial=("Massa_Salarial", "sum"),
            Vinculos_Ativos=("Vinculos_Ativos", "sum"),
        )
        df_remun_ano["Remuneracao_Media"] = (
            df_remun_ano["Massa_Salarial"] / df_remun_ano["Vinculos_Ativos"].replace(0, np.nan)
        ).fillna(0)
        fig_remun = px.line(
            df_remun_ano,
            x="Ano",
            y="Remuneracao_Media",
            color="Ocupacao_CBO",
            markers=True,
            labels={
                "Remuneracao_Media": "Remuneração Média (R$)",
                "Ano": "Ano",
                "Ocupacao_CBO": "Ocupação (CBO)",
            },
            template="plotly_white",
        )
        fig_remun.update_layout(
            height=500,
            legend_title_text="Ocupação (CBO)",
            legend=dict(x=0.5, y=-0.25, xanchor="center", yanchor="top", orientation="h"),
        )
        st.plotly_chart(fig_remun, use_container_width=True)

    with tab3:
        st.subheader("Top 10 Setores (CNAE) com Maior Concentração de Vínculos em TI")
        df_cnae = (
            df_filtrado.groupby("Setor_CNAE", as_index=False)["Vinculos_Ativos"].sum()
            .rename(columns={"Vinculos_Ativos": "Qtd_Vinculos"})
            .sort_values("Qtd_Vinculos", ascending=False)
            .head(10)
        )
        fig_cnae = px.bar(
            df_cnae,
            x="Qtd_Vinculos",
            y="Setor_CNAE",
            orientation="h",
            text_auto=".0f",
            labels={
                "Qtd_Vinculos": "Total de Vínculos Formais",
                "Setor_CNAE": "Setor (CNAE)",
            },
            template="plotly_white",
            color="Qtd_Vinculos",
            color_continuous_scale="Blues",
        )
        fig_cnae.update_layout(height=550, coloraxis_showscale=False)
        st.plotly_chart(fig_cnae, use_container_width=True)

    with tab4:
        st.subheader("Perfil Demográfico: Distribuição Percentual")

        st.markdown("#### Por Gênero em Cada CBO")
        df_genero = df_filtrado.groupby(["Ocupacao_CBO", "Sexo"], as_index=False)["Vinculos_Ativos"].sum()
        df_genero = df_genero.rename(columns={"Vinculos_Ativos": "Qtd_Vinculos"})
        df_genero["Total"] = df_genero.groupby("Ocupacao_CBO")["Qtd_Vinculos"].transform("sum")
        df_genero["Percentual"] = (df_genero["Qtd_Vinculos"] / df_genero["Total"]) * 100
        fig_genero = px.bar(
            df_genero,
            x="Percentual",
            y="Ocupacao_CBO",
            color="Sexo",
            orientation="h",
            barmode="stack",
            text=df_genero["Percentual"].apply(lambda x: f"{x:.1f}%" if x >= 8 else ""),
            color_discrete_map={"Feminino": "#3b82f6", "Masculino": "#dc2626"},
            template="plotly_white",
            labels={
                "Percentual": "Percentual de Vínculos (%)",
                "Ocupacao_CBO": "Ocupação (CBO)",
            },
        )
        fig_genero.update_traces(
            textfont=dict(size=20, color="black"),
            textposition="inside",
        )
        fig_genero.update_layout(
            height=500,
            legend_title_text="Sexo",
            legend=dict(x=0.5, y=-0.25, xanchor="center", yanchor="top", orientation="h"),
        )
        st.plotly_chart(fig_genero, use_container_width=True)

        st.markdown("#### Por Grau de Instrução em Cada CBO")
        df_inst = df_filtrado.groupby(["Ocupacao_CBO", "Grau_Instrucao"], as_index=False)["Vinculos_Ativos"].sum()
        df_inst = df_inst.rename(columns={"Vinculos_Ativos": "Qtd_Vinculos"})
        df_inst["Total"] = df_inst.groupby("Ocupacao_CBO")["Qtd_Vinculos"].transform("sum")
        df_inst["Percentual"] = (df_inst["Qtd_Vinculos"] / df_inst["Total"]) * 100
        fig_inst = px.bar(
            df_inst,
            x="Percentual",
            y="Ocupacao_CBO",
            color="Grau_Instrucao",
            orientation="h",
            barmode="stack",
            text=df_inst["Percentual"].apply(lambda x: f"{x:.1f}%" if x >= 8 else ""),
            template="plotly_white",
            labels={
                "Percentual": "Percentual de Vínculos (%)",
                "Ocupacao_CBO": "Ocupação (CBO)",
            },
        )
        fig_inst.update_traces(
            textfont=dict(size=20, color="black"),
            textposition="inside",
        )
        fig_inst.update_layout(
            height=500,
            legend_title_text="Grau de Instrução",
            legend=dict(x=0.5, y=-0.25, xanchor="center", yanchor="top", orientation="h"),
            uniformtext=dict(minsize=14, mode="hide"),
        )
        st.plotly_chart(fig_inst, use_container_width=True)

    with tab5:
        st.subheader("RAIS: Vínculos e Perfil por Divisão CNAE")
        st.caption(
            "Agregação por ano, UF, divisão CNAE 2.0, setor e ocupação CBO. "
            "Salário e escolaridade são ponderados pelos vínculos ativos em 31/12."
        )
        st.dataframe(df_rais_agregado, use_container_width=True, height=520)
        st.download_button(
            label="Baixar agregação RAIS em CSV",
            data=df_rais_agregado.to_csv(index=False).encode("utf-8-sig"),
            file_name="rais_ti_agregada_por_cnae_cbo.csv",
            mime="text/csv",
        )

    with tab6:
        st.subheader("TIC Empresas: Adoção e Barreiras à Inteligência Artificial")
        if df_tic_adocao.empty or df_tic_barreiras.empty:
            st.warning(
                "Não foi possível carregar os indicadores TIC. Confirme se "
                "tic_empresas_2021_2025.xlsx está na pasta do aplicativo e contém as colunas "
                "de adoção, barreiras e peso amostral."
            )
        else:
            st.markdown("#### Adoção de IA (H1) por ano e setor")
            fig_adocao = px.bar(
                df_tic_adocao,
                x="Ano",
                y="Adocao_IA_pct",
                color="Setor_TIC",
                barmode="group",
                labels={
                    "Adocao_IA_pct": "Empresas que adotaram IA (%)",
                    "Setor_TIC": "Setor TIC Empresas",
                    "Ano": "Ano da pesquisa",
                },
                template="plotly_white",
            )
            fig_adocao.update_layout(
                height=480,
                yaxis_range=[0, 100],
                legend_title_text="Setor TIC",
                legend=dict(x=0.5, y=-0.3, xanchor="center", yanchor="top", orientation="h"),
            )
            st.plotly_chart(fig_adocao, use_container_width=True)

            st.markdown("#### Barreiras à adoção de IA")
            anos_tic = sorted(df_tic_adocao["Ano"].unique().tolist())
            anos_barreiras_gerais = sorted(df_tic_barreiras["Ano"].unique().tolist())
            ano_barreira_padrao = (
                anos_barreiras_gerais[-1] if anos_barreiras_gerais else anos_tic[-1]
            )
            ano_tic = st.selectbox(
                "Ano da pesquisa",
                options=anos_tic,
                index=anos_tic.index(ano_barreira_padrao),
                key="ano_tic_barreiras",
            )
            setores_ano = df_tic_adocao.loc[
                df_tic_adocao["Ano"].eq(ano_tic)
                & df_tic_adocao["Porte"].eq(porte_tic_sel)
                & df_tic_adocao["Setor_TIC"].isin(setores_tic_sel)
            ]
            setores_tic = sorted(setores_ano["Setor_TIC"].unique().tolist())
            setor_tic = st.selectbox(
                "Setor TIC Empresas",
                options=setores_tic,
                key="setor_tic_barreiras",
            )
            regioes_barreiras = sorted(setores_ano["Regiao"].unique().tolist())
            regiao_tic = st.selectbox(
                "Região",
                options=regioes_barreiras,
                key="regiao_tic_barreiras",
            )
            barreiras_setor = df_tic_barreiras.loc[
                df_tic_barreiras["Ano"].eq(ano_tic)
                & df_tic_barreiras["Porte"].eq(porte_tic_sel)
                & df_tic_barreiras["Setor_TIC"].eq(setor_tic)
                & df_tic_barreiras["Regiao"].eq(regiao_tic)
            ]
            if barreiras_setor.empty:
                st.info(
                    f"Não há respostas válidas para as barreiras em {ano_tic} "
                    f"({regiao_tic}, {setor_tic}). A planilha marca todos os itens H13 "
                    "desse ano como 'Sem informação / Não se aplica'; isso não significa "
                    "que as barreiras sejam iguais a zero."
                )
            else:
                fig_barreiras = px.bar(
                    barreiras_setor.sort_values("Proporcao_pct"),
                    x="Proporcao_pct",
                    y="Barreira",
                    orientation="h",
                    text=barreiras_setor.sort_values("Proporcao_pct")["Proporcao_pct"].map(
                        lambda valor: f"{valor:.1f}%"
                    ),
                    labels={
                        "Proporcao_pct": "Empresas não adotantes que apontaram a barreira (%)",
                        "Barreira": "Barreira declarada",
                    },
                    template="plotly_white",
                )
                fig_barreiras.update_traces(textposition="outside", cliponaxis=False)
                fig_barreiras.update_layout(height=500, xaxis_range=[0, 100])
                st.plotly_chart(fig_barreiras, use_container_width=True)
            st.caption(
                "Percentuais ponderados pelo peso amostral entre empresas não adotantes que "
                "responderam validamente a cada barreira. Respostas sem informação ou não "
                "aplicáveis não entram no denominador."
            )

            st.markdown("#### Correspondência setorial TIC Empresas e CNAE 2.0")
            correspondencia = (
                df_tic_adocao[["Setor_TIC", "Divisoes_CNAE_2_0"]]
                .drop_duplicates()
                .sort_values("Setor_TIC")
            )
            st.dataframe(correspondencia, use_container_width=True, hide_index=True)
            st.caption(
                "A classificação TIC é mais agregada que a divisão CNAE da RAIS. As faixas são "
                "correspondências aproximadas; o setor 'Serviços' não pode ser desagregado em "
                "divisões específicas com COD_CNAE, portanto não deve ser interpretado como uma "
                "equivalência exata."
            )

    with st.expander("📋 Visualizar Dados Detalhados da Tabela"):
        st.dataframe(df_filtrado, use_container_width=True)

        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Baixar Dados Filtrados em CSV",
            data=csv,
            file_name="rais_filtrada_2022_2025.csv",
            mime="text/csv",
        )
else:
    st.info("Aguardando carregamento da base de dados...")
