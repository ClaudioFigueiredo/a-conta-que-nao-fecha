# -*- coding: utf-8 -*-
"""
modelo_cenarios.py -- Cenarios de 10 anos do plano de recuperacao fiscal de Minas Gerais (versao 3.7)
Livro: "A conta que nao fecha: causas da crise fiscal de Minas Gerais e um plano para sair dela",
de Claudio Ribeiro Figueiredo (1a edicao, 2026). Premissas, metodo e quadros: Anexo B do livro.

NATUREZA: CALCULO sobre premissas declaradas. Nao e previsao. Ordem de grandeza.
UNIDADE:  R$ bilhoes a precos de dez/2025 (reais, IPCA) e % da RCL do proprio ano.
INDICADOR: "insuficiencia de cobertura do servico" = primario + receitas financeiras livres
           - servico da divida - aplicacoes fora do primario - receita cedida/recomposicao.
           Negativa = insuficiencia. ACUMULA: o que falta num ano vira estoque (caixa negativo
           ou divida) e e carregado para o ano seguinte.
TRES RELOGIOS (v3, item 8):
  (1) adocao das medidas: ano 1 = 2027 (1o ano da LDO 2027);
  (2) Propag (aditivo de 31/12/2025): 20/40/60/80/100% em 2026-2030 = anos 0 a 4 do modelo;
  (3) reforma tributaria (calendario fixo): beneficios de ICMS caem de 2029 a 2032 e o ICMS
      acaba em 2033 = anos 3 a 7 do modelo. Nao e "anos a partir da adocao".
VERSOES (resumo): v3 (servico da divida em caixa, insuficiencia que acumula, ativos liquidos); v3.2 (gatilho que le
  o estoque acumulado, com volta da base em 3 anos); v3.3 (piso de investimento do Cap. 19, recomposicao do fundo
  previdenciario creditada no ano seguinte, divida consolidada liquida, sensibilidades de precatorios e de gatilho
  atrasado); v3.4 (sensibilidades da clausula de escape do gatilho e da previdencia civil pela avaliacao atuarial de
  31/12/2025); v3.5 (cenario principal do livro: encargo real de 8,25% ao ano dentro do saldo que o gatilho, a divida
  liquida e a declaracao leem; contador em zero, com o caixa herdado a parte; piso de seguranca ativa e assistencia; projecao
  da previdencia civil pela avaliacao de 31/12/2025, so pela inclinacao; escape com limiar de 3%); v3.6 (a escape passa a integrar o cenario
  principal, com a comparacao sem ela na variante "sem_escape"; atraso da certificacao com a regra de protecao: o saldo
  provisorio liga ou mantem, so o certificado desliga); v3.7 (teste da base de precos da projecao previdenciaria, nas variantes
  "prev_deflac_2" e "prev_deflac_5"; os demais resultados sao os da v3.6). Parametros em branco reproduzem a versao 3.4; as variantes "v32" e os
  resultados de historico/ sao conferidos antes de calcular.

Rodar:  python modelo_cenarios.py   (Python 3, so biblioteca padrao)
Entradas (pasta entradas/): IPCA numero-indice (IBGE, SIDRA, tabela 1737, consulta de 18/10/2026) e series fiscais de
  Minas Gerais em valores nominais e reais (SICONFI, RREO e RGF; cada linha traz a URL da consulta).
Saida:  cenarios_resultado.csv (nesta pasta) + conferencias e quadros no terminal.

Siglas das fontes citadas nos comentarios (referencias completas no livro):
  [D1] series fiscais de MG (RREO e RGF, SICONFI): arquivo de entrada; T1 a T8 = tabelas da compilacao
  [D2] divida com a Uniao: contratos e aditivos, STN (creditos da Uniao), SEF-MG (boletim e avaliacao da divida)
  [D3] pessoal e previdencia: RREO Anexos 4 e 10, RGF Anexo 1, avaliacoes atuariais do RPPS e do FFP-MG
  [D4] ativos e receitas: Balanco Geral do Estado de 2025, SEF-MG (renuncias, divida ativa), ANM (CFEM)
  [VA] [VB] [VC] analise de viabilidade juridica do livro (Capitulos 11 a 15 e Anexo B)
  [LDO-I]   LDO 2027 de Minas Gerais (Lei estadual 26.041/2026), Anexo I, Metas Fiscais
  [LDO-III] LDO 2027 de Minas Gerais, Anexo III, Metodologia e Premissas
  [LOA]     LOA 2026 de Minas Gerais, Volume I (pp. 252-254, fontes de recursos)
  [RREO6]   RREO, Anexo 6, 6o bimestre de cada ano (SICONFI)
  [CF]      Constituicao Federal, texto compilado (Planalto)
"""
import csv
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQ_IPCA = os.path.join(AQUI, "entradas", "IBGE_SIDRA_t1737_IPCA_numero-indice_consulta_2026-10-18.json")
ARQ_SERIE_REAL = os.path.join(AQUI, "entradas", "series-financas-mg-reais-ipca-dez2025.csv")
ARQ_SAIDA = os.path.join(AQUI, "cenarios_resultado.csv")
ANOS = list(range(1, 11))
ANO1_CALENDARIO = 2027


# =============================================================================
# 1. DADOS DE BASE
# =============================================================================
def carrega_ipca():
    with open(ARQ_IPCA, encoding="utf-8") as f:
        dados = json.load(f)
    return {r["D3C"]: float(r["V"]) for r in dados[1:]}


def carrega_rcl_real():
    out = {}
    with open(ARQ_SERIE_REAL, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["indicador"].startswith("RCL - Receita Corrente") and r["ano"] in ("2015", "2025"):
                out[int(r["ano"])] = (float(r["valor_nominal"]) / 1e9, float(r["valor_real_dez2025"]) / 1e9,
                                      float(r["fator_ipca"]))
    return out


def carrega_nominal(indicador):
    """Serie nominal (R$ bi) de um indicador do CSV de financas [D1]."""
    out = {}
    with open(ARQ_SERIE_REAL, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["indicador"] == indicador:
                out[int(r["ano"])] = float(r["valor_nominal"]) / 1e9
    return out


IPCA = carrega_ipca()
IDX_DEZ25 = IPCA["202512"]
RCLS = carrega_rcl_real()
RCL_NOM_2025, RCL_REAL_2025, FATOR_2025 = RCLS[2025]       # DADO [D1 T1, T8]
RCL_REAL_2015 = RCLS[2015][1]                               # DADO [D1 T8]
G_MEDIA_2015_2025 = (RCL_REAL_2025 / RCL_REAL_2015) ** (1 / 10) - 1   # CALCULO

# --- Deflator para valores nominais da LDO: IPCA de 6% a.a. em 2027-2031 (Quadro 5) [LDO-I p. 74];
#     2026: IPCA observado ate set/2026 [D1 3b] + 6% a.a. nos 3 meses restantes (HIPOTESE).
IPCA_LDO = 0.06
P_DEZ26 = IPCA["202609"] / IDX_DEZ25 * (1 + IPCA_LDO) ** 0.25


def p_medio(ano_cal):
    """Nivel medio de precos do ano (base dez/2025 = 1), para deflacionar fluxos nominais da LDO."""
    return P_DEZ26 * (1 + IPCA_LDO) ** (ano_cal - 2027) * (1 + IPCA_LDO) ** 0.5


# --- Propag ---
S0 = 182.15
N_PARCELAS = 360
ESCALA = {1: 0.20, 2: 0.40, 3: 0.60, 4: 0.80}
MES_INCORPORA = 49
ABATIMENTO = {"A": 0.20, "A30": 0.30, "B": 0.0}
FEF = {"A": 0.01, "A30": 0.01, "B": 0.02}
INV = {"A": 0.01, "A30": 0.01, "B": 0.02}
OFFSET_PROPAG = 1
SALDO_PROPAG_LDO = 143.443073123      # DADO [LDO-I p. 72, Quadro 3, nota 1]

# --- LDO 2027 (R$ mil): metas (Anexo IV/Tab. 03 = Tab. 39) e RCL (Tab. 04) [D1 6][LDO-I pp. 76-78] ---
LDO = {
    1: dict(rcl=118_499_647, rec=126_122_199, desp=122_389_170, prim=3_733_030),
    2: dict(rcl=125_045_204, rec=132_985_812, desp=127_922_516, prim=5_063_295),
    3: dict(rcl=132_245_711, rec=141_018_830, desp=135_177_966, prim=5_840_865),
}
# Tabela 39, regime caixa (R$ bi nominais) [LDO-I pp. 76-78]: DADO
TAB39 = {
    2027: dict(juros=1.462756, amort=6.292864, aplic_fin=3.940858, outras_fin=0.004944, invest=4.426485),
    2028: dict(juros=1.294622, amort=7.688739, aplic_fin=3.836105, outras_fin=0.005097, invest=4.550168),
    2029: dict(juros=1.144755, amort=8.512775, aplic_fin=3.730426, outras_fin=0.005251, invest=4.920093),
}
# Quadro 1, servico projetado em regime de caixa (R$ bi nominais) [LDO-I p. 67]: DADO
Q1 = {2027: 7.755619551, 2028: 8.983924121, 2029: 9.658110315, 2030: 11.780044089, 2031: 11.099439871}
TAB30_SERVICO = {2027: 5.654490, 2028: 6.946627, 2029: 8.421334}   # base da v2 [LDO-I p. 59] (historico)

# --- Receitas financeiras: parte livre [LDO-III, receitas 1.3.2.1 exceto JCP, por fonte; LOA pp. 252-254]:
#     fontes 10 e 15 ("Recursos ordinarios") da UO 9901 = R$ 970,5 mi de R$ 3.962,9 mi (CALCULO)
RECFIN_LIVRE_2027, RECFIN_TOTAL_ANEXO3 = 0.9705, 3.9629
FRAC_RECFIN_LIVRE = RECFIN_LIVRE_2027 / RECFIN_TOTAL_ANEXO3

# --- M02/M10: base sujeita ao limite (LC 212, art. 7o, par. 3o) ---
EDU_EXIGIDO_2021, RCL_NOM_2021 = 16.93, 82.45                  # DADO [D3 4.3][D1 T1]
PARTE_MINIMOS = (EDU_EXIGIDO_2021 / 0.25) * (0.25 + 0.12) / RCL_NOM_2021   # CALCULO ~30,4%
# Transferencias vinculadas da Uniao + FEF [LDO-III, receitas 1.7 e 2.4 das fontes 1, 2, 3, 16, 21, 24, 36,
# 51, 56, 57, 73, 89, 92, 98]: R$ 3,188 bi em 2027 (CALCULO)
EXCL_TRANSF = 3.1883 / (LDO[1]["rcl"] / 1e6)
# Fundos especiais dos Poderes: FEPJ (UO 4031) sem a remuneracao financeira (4,661 - 0,862) + receitas
# nao financeiras das UOs 1011, 1021, 1031, 1051, 1091 (0,037) = R$ 3,836 bi em 2027 (CALCULO) [LDO-III]
EXCL_PODERES = 3.836 / (LDO[1]["rcl"] / 1e6)
INICIO_M02 = 2

# --- M06 ---
GAP_MILITAR_2025 = 7.745628988
CONTRIB_MILITAR_2024, ALIQ_MILITAR, ALIQ_PL_2239 = 1.47, 0.08, 0.105

# --- M12: renuncia de ICMS e fracao liquida livre ---
RENUNCIA_ICMS_2025 = 21.98
EFETIVIDADE_M12 = 0.50
# Fracao livre de R$ 1 de ICMS recuperado (CALCULO; base legal [CF]):
#   -25% municipios (art. 158, IV) -> 0,75; -20% da parte estadual ao Fundeb (art. 212-A, II, EC 108) -> 0,60;
#   ensino 25% de 0,75 (art. 212) = 0,1875, dos quais 0,15 ja cobertos pela contribuicao ao Fundeb
#   (HIPOTESE: metodo do MDF) -> -0,0375; saude 12% de 0,75 (art. 198, par. 2o, II; ADCT, art. 77, II) -> -0,09
FRACAO_LIVRE_ICMS = 0.75 * (1 - 0.20) - (0.25 * 0.75 - 0.20 * 0.75) - 0.12 * 0.75     # = 0,4725
FASE_ICMS_CAL = {2027: 1.0, 2028: 1.0, 2029: 0.9, 2030: 0.8, 2031: 0.7, 2032: 0.6}     # ADCT, art. 128 [VC M12]
RENUNCIA_IPVA_LDO_ANO1 = 3.43
INICIO_RECEITA = 2

# --- M03 (so sensibilidade em v3) ---
COPASA_REAL = 8.389713585 * IDX_DEZ25 / IPCA["202606"]

# --- Ativos liquidos: ordem de precedencia [D2 4.4] e fluxos anuais cedidos ---
ORDEM = [("Imoveis", 1.943812437), ("Creditos do Comprev", 6.532908966), ("Juros da acao do Fundef", 10.868519850),
         ("Fluxo CFEM", 18.006494040), ("Fluxo CFURH/Itaipu", 3.152669229), ("Outros recebiveis", 1.394958692),
         ("Creditos da LC 176", 2.973049385), ("15% do FPE 2029-2055", 30.133627475)]
OFERTA_TOTAL_D2 = 96.0
COMPREV_RECOMPOSICAO = 6.532908966   # LC estadual 184/2025, art. 2o: recompor o FFP-MG em ate 12 meses [VB M08]
# Fluxos anuais (R$ bi reais): CFEM 2025 [D4 10b]; FPE 2025 [D1 T1]; CFURH, outros recebiveis e LC 176 = LDO 2027 [LDO-III]
FLUXO_ANUAL = {
    "Fluxo CFEM": 0.51549750229 * FATOR_2025,
    "Fluxo CFURH/Itaipu": (0.084873611 + 0.036400) / p_medio(2027),      # fontes 31 + 11 (desvinculacao)
    "Outros recebiveis": (0.039000 + 0.016710) / p_medio(2027),          # duas fontes de recursos
    "Creditos da LC 176": 0.418250595 / p_medio(2027),                   # "Transf. Obr. LC 176/20", fonte 15
    "15% do FPE 2029-2055": 0.15 * 9.13 * FATOR_2025,
}
INICIO_FLUXO = {"15% do FPE 2029-2055": 3}

# --- Conferencias ---
PARCELAS_2026 = [(102.0, "202601"), (102.01, "202603"), (104.5, "202606"), (104.5, "202609")]
SERVICO_EXEC_SET2026, FEF_PAGO_2026, PROPAG_PAGO_SET2026 = 6.11761, 1.66324, 0.93392   # [D2 3, 4.2]
APLIC_FIN_HIST = {2018: 0.214, 2019: 0.409, 2020: 0.223, 2021: 0.784, 2022: 3.234, 2023: 3.365, 2024: 3.327,
                  2025: 4.861}   # "Aplicacoes Financeiras (II)" realizadas [RREO6]
JUROS_ATIVOS_HIST = {2019: 0.001, 2020: 0.001, 2021: 0.786, 2022: 3.238, 2023: 3.367, 2024: 3.329,
                     2025: 4.863}  # "Juros, Encargos e Variacoes Monetarias Ativos" [RREO6]
SELIC_LDO = 0.1475                 # [LDO-I p. 74, Quadro 5]
JURO_REAL_ESTOQUE = (1 + SELIC_LDO) / (1 + IPCA_LDO) - 1    # sensibilidade do custo do estoque

# --- v3.3 (D1) Piso de investimento do Cap. 19 ---
PISO_INV = 0.06                    # media de 3 anos >= 6% da RCL (centro da serie 2015-2025); minimo anual 2,7%
INV_EMP = carrega_nominal("Investimentos - empenhado (exceto intra)")     # DADO [D1, RREO Anexo 1]
INV_PAGO = carrega_nominal("Investimentos - pago (exceto intra)")         # DADO [D1, RREO Anexo 1]
RCL_NOM = carrega_nominal("RCL - Receita Corrente Líquida (RREO Anexo 3)")
SERIE_INV_PCT = {a: INV_EMP[a] / RCL_NOM[a] for a in range(2015, 2026)}  # CALCULO
# A Tab. 39 da LDO traz o investimento PAGO NO ANO (os restos a pagar estao na linha "Pagamento de Restos a Pagar de
# Despesas Primarias" [LDO-I p. 78]); o piso e pelo empenhado. Conversao pela razao pago/empenhado de 2023-2025 (CALCULO;
# HIPOTESE: a razao se mantem e, na media de 3 anos, o caixa do investimento acompanha o empenhado).
INV_K = sum(INV_PAGO[a] for a in (2023, 2024, 2025)) / sum(INV_EMP[a] for a in (2023, 2024, 2025))


def inv_ldo_ratio(t):
    """Investimento pago no ano da LDO (Tab. 39) / RCL da LDO; anos 1-3 e, depois, a razao do ano 3."""
    tt = min(t, 3)
    return TAB39[ANO1_CALENDARIO + tt - 1]["invest"] / (LDO[tt]["rcl"] / 1e6)


# --- v3.3 (D2) Comprev: compensacao previdenciaria do RGPS para o RPPS recebida pelo FFP-MG [LDO-I p. 101]: DADO
COMPREV_FLUXO_HIST = {2023: 0.042046002, 2024: 0.097430558, 2025: 0.081031030}
COMPREV_FLUXO = COMPREV_FLUXO_HIST[2025] * FATOR_2025      # perda anual, R$ bi reais (HIPOTESE: constante)
APORTE_FFP_2025 = 11.866802345     # "Recursos para Cobertura de Insuficiencias Financeiras" 2025 [LDO-I p. 101]: DADO

# --- v3.3 (D3) Divida consolidada liquida: posicao de 31/12/2025 [D1, RGF Anexo 2]: DADO ---
DC_2025 = carrega_nominal("Dívida consolidada (DC)")[2025]
DCL_2025 = carrega_nominal("Dívida consolidada líquida (DCL)")[2025]
PREC_DC_2025 = carrega_nominal("Precatórios posteriores a 05/05/2000 vencidos e não pagos (na DC)")[2025]
DEMAIS_DC_2025 = DC_2025 - S0 - PREC_DC_2025       # CALCULO: DC menos Propag (linha de reestruturacao) e precatorios
# Juros e encargos do Quadro 1 (R$ bi nominais) [LDO-I p. 67]: separam a amortizacao das demais dividas
Q1_JUROS = {2027: 1.364468600 + 0.098833468, 2028: 1.211655783 + 0.083529469, 2029: 1.077294524 + 0.068040330,
            2030: 0.959200744 + 0.052189337, 2031: 0.842300856 + 0.036387852}

# --- v3.3 (D4) Precatorios: teto de 1% da RCL (EC 136/2025); se o STF derrubar o teto e voltar o prazo de 2029,
#     pagamento de 1,3% a 2,2% da RCL, isto e, +0,2 a +1,0 ponto sobre o teto [NOTA-precatorios-conciliacao §3.5, §4]
PREC_LEVE = {1: 0.002, 2: 0.002, 3: 0.002}
PREC_RGF = {1: 0.010, 2: 0.010, 3: 0.010}


# =============================================================================
# 2. MOTOR
# =============================================================================
def simula_propag(ramo):
    s = S0 * (1 - ABATIMENTO[ramo])
    p = s / N_PARCELAS
    cg = 0.0
    anos = {}
    for m in range(1, 12 * 11 + 1):
        ano_aditivo = (m - 1) // 12 + 1
        t = ano_aditivo - OFFSET_PROPAG
        if m == MES_INCORPORA:
            s += cg
            cg = 0.0
            p = s / (N_PARCELAS - (m - 1))
        x = ESCALA.get(ano_aditivo, 1.0)
        d = anos.setdefault(t, dict(pago=0.0, estoque_ini=s + cg, cg_max=0.0))
        d["pago"] += x * p
        cg += (1 - x) * p
        s -= p
        d["estoque_fim"] = s + cg
        d["prestacao_cheia_mes"] = p
        d["cg_max"] = max(d["cg_max"], cg)
    return anos


PROPAG = {r: simula_propag(r) for r in ("A", "B", "A30")}


def ldo_ratio(t, chave):
    tt = min(t, 3)
    return LDO[tt][chave] / LDO[tt]["rcl"]


def demais_dividas_real():
    """Demais dividas, R$ bi reais, INDEPENDENTES da RCL do cenario (corrige o defeito da v2):
    Quadro 1 (regime caixa) menos a parcela do Propag do ramo A que a LDO supoe, ambos nominais e
    deflacionados pelo IPCA da propria LDO; 2027-2031 = anos 1-5. Depois: valor real de 2031 (HIPOTESE)."""
    out = {}
    for t in ANOS:
        cal = ANO1_CALENDARIO + t - 1
        if cal in Q1:
            pm = p_medio(cal)
            out[t] = (Q1[cal] - PROPAG["A"][t]["pago"] * pm) / pm
        else:
            out[t] = out[5]
    return out


DEMAIS = demais_dividas_real()


def demais_estoque():
    """v3.3 (D3): saldo real das demais dividas. Amortizacao = servico das demais (DEMAIS) menos juros e encargos do
    Quadro 1, deflacionados; anos 6-10 com os juros do ano 5 (como o servico). Ano 0 (2026) com a amortizacao do ano 1
    (HIPOTESE). Saldo nunca negativo."""
    juros = {t: Q1_JUROS[ANO1_CALENDARIO + min(t, 5) - 1] / p_medio(ANO1_CALENDARIO + min(t, 5) - 1) for t in ANOS}
    amort = {t: DEMAIS[t] - juros[t] for t in ANOS}
    est = {0: DEMAIS_DC_2025 - amort[1]}
    for t in ANOS:
        est[t] = max(0.0, est[t - 1] - amort[t])
    return est, amort


DEMAIS_ESTOQUE, DEMAIS_AMORT = demais_estoque()
# DCL no fim do ano 0, por ramo: posicao de 2025 + variacao do Propag (inclui o abatimento do ramo A) + amortizacao das
# demais no ano 0. HIPOTESE: caixa do ano 0 neutro; ativos cedidos no abatimento fora das deducoes da DCL.
DCL_ANO0 = {r: DCL_2025 + (PROPAG[r][0]["estoque_fim"] - S0) + (DEMAIS_ESTOQUE[0] - DEMAIS_DC_2025)
            for r in ("A", "B", "A30")}


def recfin_real(t, leitura):
    """Receitas financeiras (fora do primario), R$ bi reais. 'zero' (a); 'ldo' (b, teto: Tab. 39 inteira);
    'livre' (provavel: so fontes 10 e 15 do Tesouro). Anos 1-3 pela LDO; depois, valor real do ano 3 (HIPOTESE)."""
    if leitura == "zero":
        return 0.0
    cal = ANO1_CALENDARIO + min(t, 3) - 1
    tot = (TAB39[cal]["aplic_fin"] + TAB39[cal]["outras_fin"]) / p_medio(cal)
    return tot if leitura == "ldo" else FRAC_RECFIN_LIVRE * TAB39[cal]["aplic_fin"] / p_medio(cal)


def caminho(g, choque=False):
    """RCL real por ano t=0..10 (t=0 = 2026). Choque: -3% real no ano 3 e volta a tendencia em 2 anos
    (HIPOTESE: V); a despesa de referencia segue a tendencia (rigidez)."""
    gr = [g] * 11
    if choque is True:
        rec = math.sqrt((1 + g) ** 3 / 0.97) - 1
        gr[3], gr[4], gr[5] = -0.03, rec, rec
    elif choque:                                     # v3.5: ano, queda real, anos de volta, perda permanente de nivel
        a, q, n, perda = choque["ano"], choque["queda"], choque["volta"], choque.get("perda", 0.0)
        rec = (((1 + g) ** (n + 1)) * (1 - perda) / (1 + q)) ** (1.0 / n) - 1
        gr[a] = q
        for i in range(1, n + 1):
            if a + i <= 10:
                gr[a + i] = rec
    R, RT = [], []
    x = xt = RCL_REAL_2025
    for t in range(11):
        x *= 1 + gr[t]
        xt *= 1 + g
        R.append(x)
        RT.append(xt)
    return R, RT


CAMINHOS = {"2,5%": (0.025, False), "1,0%": (0.010, False), "0,0%": (0.0, False),
            "choque 2,5%": (0.025, True), "choque 1,0%": (0.010, True)}
EXCL_PADRAO = PARTE_MINIMOS + EXCL_TRANSF + EXCL_PODERES


def ativos_cedidos(ramo):
    """Fracoes de cada ativo usadas para atingir o abatimento, pela ordem de precedencia [D2 4.4]."""
    alvo, acum, usados = ABATIMENTO[ramo] * S0, 0.0, {}
    for nome, v in ORDEM:
        if acum >= alvo - 1e-12:
            break
        fr = min(1.0, (alvo - acum) / v)
        usados[nome] = fr
        acum += fr * v
    return usados


CEDIDOS = {r: ativos_cedidos(r) for r in ("A", "A30")}


def perda_receita(ramo, t):
    if ramo not in CEDIDOS:
        return 0.0
    return sum(fr * FLUXO_ANUAL[n] for n, fr in CEDIDOS[ramo].items()
               if n in FLUXO_ANUAL and t >= INICIO_FLUXO.get(n, 1))


def roda(caminho_id, ramo, alpha=None, f06=0.0, s12=0.0, ipva=False, gatilho=False, reserva=0.0,
         recfin="livre", liquido=True, excl=EXCL_PADRAO, gatilho_modo="anual", volta_anos=None,
         piso=None, piso_k=None, comprev_modo="credito", prec_extra=None, gatilho_lag=1, escape=False, prev_proj=None,
         custo_r=None, est0=0.0, fin0=0.0, recomp_mesmo_ano=False, perim=0.0, share=0.0, tab_prev=None,
         escape_limiar=None, inicio_gat=None, adesao=1.0, alpha_gat=0.0, gatilho_prov=False):
    """gatilho_modo: 'anual' (v3: liga se a cobertura do ano anterior < 0) ou 'acumulado' (liga enquanto o
    estoque acumulado do ano anterior < 0). volta_anos (so no modo acumulado; v3.1, HIPOTESE de desenho do autor):
    depois da quitacao, o limite volta a trajetoria legal (70% como se o gatilho nao tivesse existido) em
    volta_anos anos, fechando a diferenca em partes iguais; None = sem volta (rebaixamento permanente).
    v3.3: piso = None (v3.2) | 'dentro' (piso de investimento dentro do limite: a contencao recai sobre o resto da
    despesa sujeita, desenho do Cap. 19) | 'fora' (piso pago com despesa nova, fora do limite: estresse); piso_k = razao
    pago/empenhado que converte o investimento da LDO (padrao INV_K). comprev_modo = 'credito' (v3.3: recomposicao no
    ano 1, aporte menor no ano 2, perda anual do fluxo do Comprev) | 'saida' (v3.2: so a recomposicao no ano 1).
    prec_extra = {ano: fracao da RCL} paga a mais em precatorios, fora do limite. gatilho_lag = anos entre o estoque
    lido e o ano em que o gatilho age (1 = certificacao a tempo; 2 = um ano de atraso).
    escape (v3.4): no ano de queda real da RCL o gatilho fica suspenso (regra legal no ano; nao conta como volta).
    prev_proj (v3.4) = {ano civil: deficit da previdencia civil, R$ bi constantes}: do ano 4 em diante, o primario
    perde (deficit/RCL do ano - deficit/RCL do ano 3) x RCL do ano."""
    g, choque = CAMINHOS[caminho_id]
    R, RT = caminho(g, choque)
    k = INV_K if piso_k is None else piso_k
    linhas = []
    cap = cap_legal = None
    anos_liberado = 0
    dsub_prev = None
    r_prev = None
    g_rec_prev = g
    hist_cob, hist_est = [], []
    estoque = estoque_carry = est0
    sobra1 = None
    saldo_res, usado_res = reserva, 0.0
    prec_cum = 0.0
    resto_prev = None
    gap_mil_real = GAP_MILITAR_2025 / RCL_NOM_2025 * RCL_REAL_2025
    ren_ratio = RENUNCIA_ICMS_2025 / RCL_NOM_2025
    ipva_ratio = RENUNCIA_IPVA_LDO_ANO1 / (LDO[1]["rcl"] / 1e6)
    base_ano0 = PROPAG[ramo][0]["estoque_ini"]
    fr_comprev = CEDIDOS.get(ramo, {}).get("Creditos do Comprev", 0.0) if liquido else 0.0
    for t in ANOS:
        cal = ANO1_CALENDARIO + t - 1
        R_, RT_ = R[t], RT[t]
        rec_ref = ldo_ratio(t, "rec") * R_
        desp_ref = (ldo_ratio(t, "rec") - ldo_ratio(t, "prim")) * RT_
        m06 = f06 * gap_mil_real if t >= INICIO_RECEITA else 0.0
        fase = FASE_ICMS_CAL.get(cal, 0.0)
        m12 = s12 * ren_ratio * EFETIVIDADE_M12 * FRACAO_LIVRE_ICMS * fase * R_ if t >= INICIO_RECEITA else 0.0
        if ipva and t >= INICIO_RECEITA:
            m12 += s12 * ipva_ratio * EFETIVIDADE_M12 * R_
        rec = rec_ref + m06 + m12
        exc = excl * RT_
        dsub_ref = desp_ref - exc
        # investimento exigido pelo Propag, investimento da LDO e piso (v3.3, D1)
        pp = PROPAG[ramo][t]
        fef = FEF[ramo] * pp["estoque_ini"]
        inv = INV[ramo] * pp["estoque_ini"]
        fef_ldo = FEF["A"] * PROPAG["A"][t]["estoque_ini"]
        comp_fef = comp_inv = 0.0
        if ramo == "B" and t == 1:
            comp_fef = (FEF["B"] - FEF["A"]) * base_ano0
            comp_inv = (INV["B"] - INV["A"]) * base_ano0
        inv_ldo = (TAB39[cal]["invest"] / p_medio(cal)) if cal in TAB39 else \
            TAB39[2029]["invest"] / p_medio(2029) / (LDO[3]["rcl"] / 1e6 / p_medio(2029)) * RT_
        inv_extra = max(0.0, inv + comp_inv - inv_ldo)
        inv_ldo_emp = inv_ldo_ratio(t) / k * RT_          # investimento da LDO, em empenhado, na despesa de referencia
        piso_extra = max(0.0, PISO_INV * R_ - inv_ldo_emp - inv_extra) if piso else 0.0
        dsub_ref_p = dsub_ref + (piso_extra if piso == "dentro" else 0.0)
        gat_on = suspenso = False
        if alpha is None:
            dsub = dsub_ref_p
        else:
            a_t = alpha
            hist = hist_cob if gatilho_modo == "anual" else hist_est
            sinal = hist[-gatilho_lag] if len(hist) >= gatilho_lag else None
            if gatilho_prov and hist:                                  # v3.6: certificacao atrasada: o provisorio liga ou mantem; so o certificado desliga
                sinal = hist[-1] if sinal is None else min(hist[-1], sinal)
            esc = escape and (R[t] < R[t - 1] if escape_limiar is None else R[t] <= R[t - 1] * (1 - escape_limiar) + 1e-9)
            if gatilho and t >= (inicio_gat or INICIO_M02) and sinal is not None and sinal < 0 and not esc:
                a_t, gat_on = alpha_gat, True
            suspenso = esc and gatilho and t >= INICIO_M02 and sinal is not None and sinal < 0
            cap_legal = dsub_ref if t == 1 else cap_legal * (1 + alpha * max(0.0, g_rec_prev))   # sombra legal
            cap = dsub_ref if t == 1 else cap * (1 + a_t * max(0.0, g_rec_prev))
            if gatilho and gatilho_modo == "acumulado" and volta_anos and t >= INICIO_M02:
                if gat_on:
                    anos_liberado = 0
                elif suspenso:
                    pass                                                   # escape: suspensao, nao volta
                else:
                    anos_liberado += 1
                    passo = 1.0 / max(1, volta_anos - anos_liberado + 1)
                    cap = cap + max(0.0, cap_legal - cap) * passo      # fecha a diferenca em partes iguais
            dsub = (adesao * min(dsub_ref_p, cap) + (1 - adesao) * min(dsub_ref_p, cap_legal)) if t >= INICIO_M02 else dsub_ref_p
        m02 = dsub_ref_p - dsub
        cresc_dsub = (dsub / dsub_prev - 1) if dsub_prev else 0.0
        dsub_prev = dsub
        resto = dsub - inv_ldo_emp - (piso_extra if piso == "dentro" else 0.0)   # despesa sujeita sem o investimento
        cresc_resto = (resto / resto_prev - 1) if resto_prev else 0.0
        resto_prev = resto
        extra_serv = 0.0
        if tab_prev is not None:                 # v3.5: piso dos servicos: a parte protegida da queda da sobra sai da cobertura
            sobra = resto - tab_prev.get(cal, tab_prev[max(tab_prev)])
            if sobra1 is None:
                sobra1 = sobra
            extra_serv = share * max(0.0, sobra1 - sobra)
        prim = rec - (dsub + exc) - extra_serv
        if prev_proj and t >= 4:
            prim -= (prev_proj[cal] / R_ - prev_proj[ANO1_CALENDARIO + 2] / R[3]) * R_
        prim_ref = rec_ref - desp_ref
        if r_prev is not None:
            g_rec_prev = rec / r_prev - 1
        r_prev = rec
        # servico e aplicacoes
        parcela = pp["pago"]
        outras = DEMAIS[t]
        serv = parcela + outras
        prec = (prec_extra or {}).get(t, 0.0) * R_
        prec_cum += prec
        aplic = (fef - fef_ldo) + comp_fef + inv_extra + (piso_extra if piso == "fora" else 0.0) + prec
        rf = recfin_real(t, recfin)
        cedido = perda_receita(ramo, t) if liquido else 0.0
        comprev = 0.0
        if fr_comprev:
            if t == 1:
                comprev += fr_comprev * COMPREV_RECOMPOSICAO      # LC estadual 184/2025, art. 2o
            if comprev_modo == "credito":
                cedido += fr_comprev * COMPREV_FLUXO            # fluxo de compensacao que deixa de entrar no FFP-MG
                if t == 2:
                    comprev -= fr_comprev * COMPREV_RECOMPOSICAO  # o fundo usa o valor: aporte do Tesouro menor
        if recomp_mesmo_ano:
            comprev = 0.0
        cob = prim + rf - serv - aplic - cedido - comprev - perim
        hist_cob.append(cob)
        estoque_carry = estoque_carry * (1 + JURO_REAL_ESTOQUE) + cob if estoque_carry < 0 else estoque_carry + cob
        enc = (custo_r or 0.0) * max(0.0, -(estoque + fin0))     # v3.5: encargo so sobre o que ficou sem financiamento
        est_ini = estoque
        estoque = estoque - enc + cob
        hist_est.append(estoque)
        uso = min(saldo_res, max(0.0, -cob))
        saldo_res -= uso
        usado_res += uso
        # DCL (v3.3, D3): pagamento extra de precatorios reduz caixa e divida na mesma medida
        dcl = (DCL_ANO0[ramo] + (pp["estoque_fim"] - PROPAG[ramo][0]["estoque_fim"])
               + (DEMAIS_ESTOQUE[t] - DEMAIS_ESTOQUE[0]) - (estoque - est0) - prec_cum)
        linhas.append(dict(
            est_ini=est_ini, enc=enc, extra_serv=extra_serv, ano=t, cal=cal, rcl=R_, parcela=parcela, outras=outras, serv=serv, fef=fef, inv=inv,
            comp=comp_fef + comp_inv, aplic=aplic, inv_extra=inv_extra, recfin=rf, prim_ref=prim_ref, m02=m02,
            m06=m06, m12=m12, cedido=cedido, comprev=comprev, prim=prim, cob=cob, estoque=estoque,
            estoque_carry=estoque_carry, uso_res=uso, cob_pos=cob + uso, estoque_res=estoque + usado_res,
            estoque_uniao=pp["estoque_fim"], gatilho=gat_on, escape=suspenso, cresc_dsub=cresc_dsub,
            inv_total=inv_ldo_emp + inv_extra + piso_extra, piso_extra=piso_extra, prec=prec, dcl=dcl,
            resto=resto, cresc_resto=cresc_resto))
    return linhas


def pct(v, r):
    return 100.0 * v / r


# =============================================================================
# 3. CENARIOS
# =============================================================================
# v3.3: o nucleo leva o piso de investimento do Cap. 19 ("dentro" do limite); a premissa do Comprev (credito) vale
# para todos os cenarios com abatimento (padrao de roda).
NUCLEO = dict(alpha=0.70, f06=0.10, s12=0.05, piso="dentro")
# v3.2 (desenho do autor; volta da base em 3 anos, reversivel): o gatilho le o
# estoque acumulado e fica ligado ate a quitacao; depois, o limite volta a trajetoria legal em 3 anos, fechando
# a diferenca em partes iguais. HIPOTESE de desenho do autor. Comparacoes: volta em 1 ano (v3.1),
# volta em 2 anos, sem volta, gatilho anual (v3).
NUCLEO_GAT = dict(NUCLEO, gatilho=True, gatilho_modo="acumulado", volta_anos=3)
NUCLEO_GAT_ANUAL = dict(NUCLEO, gatilho=True)                                  # v3 (comparacao)
NUCLEO_GAT_AC = dict(NUCLEO, gatilho=True, gatilho_modo="acumulado")           # sem volta da base (6.8)
NUCLEO_GAT_V = {k: dict(NUCLEO, gatilho=True, gatilho_modo="acumulado", volta_anos=k) for k in (1, 2)}
NUCLEO_ALTO = dict(alpha=0.50, f06=0.25, s12=0.10, piso="dentro")
POLITICAS = {"SEM": ("Sem as medidas do núcleo", {}),
             "NUCLEO": ("Núcleo conservador (M02 70% + M06 10% + M12 5% líquido) + piso de investimento", NUCLEO),
             "NUCLEO_GAT": ("Núcleo conservador + gatilho (lê o estoque; volta da base em 3 anos) + piso", NUCLEO_GAT)}
# v3.3: decomposicao e sensibilidades (variante -> ajuste sobre a politica)
# Deficit da previdencia civil (plano financeiro), R$ bi, valores da fonte, avaliacao atuarial do FFP-MG, data focal
# 31/12/2025, Anexo 5 (projecoes para o RREO), p. A52; rodape: inflacao de 0% e reajuste de beneficio sem paridade de 5%. A base de precos nao esta
# confirmada: os valores entram como publicados, sob a hipotese de que a sua variacao mede a pressao sobre o resto da despesa (o nivel fica no primario).
# Referencia por escolha do autor; teste da base de precos nas variantes prev_deflac_2 e prev_deflac_5 [D3]
PREV_AVAL_2025 = {2026: 11.27, 2027: 16.22, 2028: 16.38, 2029: 16.56, 2030: 16.80, 2031: 17.18, 2032: 17.66,
                  2033: 18.24, 2034: 18.85, 2035: 19.47, 2036: 20.11}
# v3.5: parte protegida: seguranca ativa e assistencia, R$ 11,88 bi, sobre a base comprimivel identificada de R$ 39,41 bi (RREO, Anexo 2, empenhado de 2025)
SHARE_SEG_ASSIST = 11.88 / 39.41
SHARE_TODOS = 18.05 / 39.41
PREV_AVAL_2024 = {2026: 13.50, 2027: 13.62, 2028: 13.75, 2029: 13.88, 2030: 14.24, 2031: 14.23, 2032: 14.30, 2033: 14.33, 2034: 14.35, 2035: 14.43, 2036: 14.49}
NUCLEO_35 = dict(NUCLEO_GAT, custo_r=JURO_REAL_ESTOQUE, share=SHARE_SEG_ASSIST, tab_prev=PREV_AVAL_2025, escape=True, escape_limiar=0.03)   # v3.6: com a escape do plano

V33_EXTRAS = {
    "v32": dict(comprev_modo="saida", piso=None),        # reproduz a v3.2
    "sem_piso": dict(piso=None),                          # v3.3 sem o piso (isola o credito do Comprev)
    "piso_fora": dict(piso="fora"),                       # estresse: piso pago com despesa nova
    "piso_fora_k1": dict(piso="fora", piso_k=1.0),        # estresse maximo: investimento PAGO no ano em 6%
    "prec_leve": dict(prec_extra=PREC_LEVE),              # precatorios +0,2 ponto da RCL nos anos 1-3
    "prec_rgf": dict(prec_extra=PREC_RGF),                # precatorios +1,0 ponto da RCL nos anos 1-3
    "gat_atraso": dict(gatilho_lag=2),                    # certificacao com um ano de atraso
    "escape": dict(escape=True),                          # v3.4: clausula de escape do gatilho (Cap. 13)
    "previdencia_aval": dict(prev_proj=PREV_AVAL_2025),   # v3.4: deficit civil da avaliacao de dez/2025 (G6)
}
ISOLADAS = {"M02_70": dict(alpha=0.70), "M02_50": dict(alpha=0.50), "M02_00": dict(alpha=0.0),
            "M06_10": dict(f06=0.10), "M06_25": dict(f06=0.25), "M06_50": dict(f06=0.50),
            "M12_05": dict(s12=0.05), "M12_10": dict(s12=0.10), "M12_05_IPVA": dict(s12=0.05, ipva=True),
            "NUCLEO_ALTO": NUCLEO_ALTO}


def roda_todos():
    res = {}

    def put(cid, cam, ramo, extra, **kw):
        res[(cid, cam, ramo, extra)] = roda(cam, ramo, **kw)

    for cam in CAMINHOS:
        for ramo in ("A", "B"):
            for pid, (_, kw) in POLITICAS.items():
                put(pid, cam, ramo, "principal", **kw)
            for pid in ("NUCLEO", "NUCLEO_GAT"):
                put(pid, cam, "A30", "principal", **POLITICAS[pid][1])
        for ramo in ("A", "B"):
            for pid, (_, kw) in POLITICAS.items():
                for rf in ("zero", "ldo"):
                    put(pid, cam, ramo, "recfin_" + rf, recfin=rf, **kw)
                put(pid, cam, ramo, "reserva_copasa", reserva=COPASA_REAL, **kw)
            put("SEM", cam, ramo, "bruto", liquido=False)
            for iid, kw in ISOLADAS.items():
                put(iid, cam, ramo, "principal", **kw)
            put("NUCLEO", cam, ramo, "so_minimos", excl=PARTE_MINIMOS, **NUCLEO)
            put("M02_70", cam, ramo, "so_minimos", excl=PARTE_MINIMOS, alpha=0.70)
            put("NUCLEO_GAT_ANUAL", cam, ramo, "principal", **NUCLEO_GAT_ANUAL)
            put("NUCLEO_GAT_AC", cam, ramo, "principal", **NUCLEO_GAT_AC)
            for k, kw in NUCLEO_GAT_V.items():
                put(f"NUCLEO_GAT_V{k}", cam, ramo, "principal", **kw)
            for pid, (_, kw) in POLITICAS.items():
                for ext, ajuste in V33_EXTRAS.items():
                    if pid == "SEM" and ext not in ("v32", "prec_leve", "prec_rgf"):
                        continue          # sem medidas nao tem piso nem gatilho
                    if pid == "NUCLEO" and ext in ("gat_atraso", "escape"):
                        continue
                    put(pid, cam, ramo, ext, **dict(kw, **ajuste))
    return res


# =============================================================================
# 5. CONFERENCIAS
# =============================================================================
def conferencias():
    print("=" * 78)
    print("CONFERENCIAS")
    print("=" * 78)
    print(f"RCL real media 2015-2025: {100 * G_MEDIA_2015_2025:.2f}% a.a.")
    for cal in (2027, 2028, 2029):
        d = TAB39[cal]
        assert abs(d["juros"] + d["amort"] - Q1[cal]) < 0.002, cal   # Tab. 39 = Quadro 1
    print("Tab. 39 (juros + amortizacao) = Quadro 1 em 2027-2029: OK")
    print(f"Deflator LDO: P_dez26 = {P_DEZ26:.4f}; p_medio 2027..2031 = "
          + ", ".join(f"{p_medio(c):.4f}" for c in range(2027, 2032)))
    print("Demais dividas (R$ bi reais), anos 1-5 = " + ", ".join(f"{DEMAIS[t]:.2f}" for t in range(1, 6))
          + f"; anos 6-10 = {DEMAIS[6]:.2f} (hipotese)")
    print("   v2 (Tab. 30 - Propag A, g=2,5%) era 3,74 / 3,86 / 4,08 nos anos 1-3")
    idx_med = sum(IPCA[f"2026{m:02d}"] for m in range(1, 10)) / 9
    exe = (SERVICO_EXEC_SET2026 - FEF_PAGO_2026 - PROPAG_PAGO_SET2026) * IDX_DEZ25 / idx_med * 12 / 9
    print(f"Contraprova: servico executado em 2026 menos FEF e Propag, anualizado, real ~ {exe:.2f} bi")
    pb = PROPAG["B"][0]["prestacao_cheia_mes"] * 1000
    p20 = PROPAG["B"][0]["pago"] / 12 * 1000
    obs = [v * IDX_DEZ25 / IPCA[m] for v, m in PARCELAS_2026]
    assert abs(pb - 506) < 1 and all(abs(x - p20) / p20 < 0.02 for x in obs)
    assert abs(PROPAG["B"][3]["cg_max"] - 12.1) < 0.1
    print(f"Prestacao cheia {pb:.1f} mi/mes; 20% = {p20:.1f}; observadas {', '.join(f'{x:.1f}' for x in obs)}")
    print("Receitas financeiras (R$ bi nominais) RREO: aplicacoes realizadas x linha de juros ativos:")
    for a in sorted(APLIC_FIN_HIST):
        print(f"   {a}: {APLIC_FIN_HIST[a]:.3f} x {JUROS_ATIVOS_HIST.get(a, float('nan')):.3f}")
    print(f"Parte livre (fontes 10 e 15) = {RECFIN_LIVRE_2027:.3f}/{RECFIN_TOTAL_ANEXO3:.3f} = {100 * FRAC_RECFIN_LIVRE:.1f}%; "
          f"livre real anos 1-3 = " + ", ".join(f"{recfin_real(t, 'livre'):.2f}" for t in (1, 2, 3))
          + "; total LDO real = " + ", ".join(f"{recfin_real(t, 'ldo'):.2f}" for t in (1, 2, 3)))
    print(f"Fracao livre do ICMS recuperado = {FRACAO_LIVRE_ICMS:.4f}")
    print(f"Exclusoes do limite (% RCL): minimos {100 * PARTE_MINIMOS:.2f}; transf. vinculadas + FEF "
          f"{100 * EXCL_TRANSF:.2f}; fundos dos Poderes {100 * EXCL_PODERES:.2f}; total {100 * EXCL_PADRAO:.2f}")
    for r in ("A", "A30"):
        print(f"Ativos cedidos ramo {r}: " + "; ".join(f"{n} {100 * f:.1f}%" for n, f in CEDIDOS[r].items())
              + f" | receita anual cedida ano 1 = {perda_receita(r, 1):.3f}, ano 3+ = {perda_receita(r, 3):.3f} bi")
    print("Fluxos anuais (R$ bi reais): " + "; ".join(f"{n} {v:.3f}" for n, v in FLUXO_ANUAL.items()))
    print(f"(b) 10 pontos a mais = {0.10 * S0:.2f} bi; {100 * 0.10 * S0 / (OFERTA_TOTAL_D2 - 0.2 * S0):.0f}% do que "
          f"sobra da oferta depois dos 20%")
    for g in (0.025, 0.010):
        R, RT = caminho(g, True)
        print(f"Choque sobre {100 * g:.1f}%: RCL/tendencia anos 2..6 = "
              + ", ".join(f"{R[t] / RT[t]:.3f}" for t in range(2, 7)))
    print(f"Juro real do estoque (sensibilidade) = (1+{SELIC_LDO})/(1+{IPCA_LDO})-1 = {100 * JURO_REAL_ESTOQUE:.2f}%")
    print("Investimento exigido x investimento em caixa da LDO (Tab. 39), anos 1-3, R$ bi reais:")
    for ramo in ("A", "B"):
        vals = []
        for t in (1, 2, 3):
            cal = ANO1_CALENDARIO + t - 1
            ex = INV[ramo] * PROPAG[ramo][t]["estoque_ini"] + (0.01 * PROPAG["B"][0]["estoque_ini"] if ramo == "B" and t == 1 else 0)
            vals.append(f"ano {t}: {ex:.2f} x {TAB39[cal]['invest'] / p_medio(cal):.2f}")
        print(f"   ramo {ramo}: " + "; ".join(vals))
    base_impl = CONTRIB_MILITAR_2024 / ALIQ_MILITAR
    print(f"Militares: base implicita {base_impl:.1f} bi; PL 2.239 fecha "
          f"{100 * base_impl * (ALIQ_PL_2239 - ALIQ_MILITAR) / GAP_MILITAR_2025:.1f}% da diferenca")


# =============================================================================
# 6. TABELAS
# =============================================================================
def br(v, casas=1):
    s = f"{v:.{casas}f}".replace(".", ",")
    return "0,0" if s in ("-0,0", "-0,00") and casas == 1 else s


def zera(L_, chave="cob"):
    ok = [x[chave] >= -1e-9 for x in L_]
    if not any(ok):
        return "não zera em 10 anos"
    i = ok.index(True)
    if all(ok[i:]):
        return f"a partir do ano {i + 1}"
    anos = [k + 1 for k, v in enumerate(ok) if v]
    return "só no(s) ano(s) " + ", ".join(map(str, anos))


def estoque_zera(L_):
    """Primeiro ano a partir do qual o estoque acumulado fica >= 0 (a insuficiencia acumulada foi paga)."""
    for i in range(10):
        if all(x["estoque"] >= -1e-9 for x in L_[i:]):
            return f"ano {i + 1}"
    return "não zera"


# =============================================================================
# 7. v3.3: CONFERENCIAS E TABELAS NOVAS
# =============================================================================
ARQ_V32 = os.path.join(AQUI, "historico", "cenarios_resultado_v3.2.csv")


def dcl0_pct(caminho_id, ramo):
    g, choque = CAMINHOS[caminho_id]
    return 100.0 * DCL_ANO0[ramo] / caminho(g, choque)[0][0]


def condicoes(L_, caminho_id, ramo):
    """Tres condicoes do Cap. 16 por ano: (1) cobertura anual >= 0 e estoque pago; (2) DCL/RCL em queda;
    (3) investimento no piso (6% da RCL, em empenhado)."""
    prev, out = dcl0_pct(caminho_id, ramo), []
    for L in L_:
        r = L["rcl"]
        c1 = L["cob"] >= -1e-9 and L["estoque"] >= -1e-9
        d = pct(L["dcl"], r)
        c2 = d < prev
        prev = d
        c3 = L["inv_total"] >= PISO_INV * r - 1e-9
        out.append((c1, c2, c3))
    return out


def condicoes_desde(L_, caminho_id, ramo):
    ok = [all(c) for c in condicoes(L_, caminho_id, ramo)]
    for i in range(10):
        if all(ok[i:]):
            return f"ano {i + 1}"
    return "não se encontram"


def declaracao(L_, caminho_id, ramo):
    """Tres exercicios seguidos com as tres condicoes, contados da parcela cheia (ano 4): contas do 3o exercicio."""
    ok = [all(c) for c in condicoes(L_, caminho_id, ramo)]
    for i in range(3, 8):
        if all(ok[i:i + 3]):
            return f"contas do ano {i + 3}"
    return "fora do horizonte"


def declaracao_k(L_, caminho_id, ramo, k=3):
    """v3.5: k exercicios seguidos com as tres condicoes, contados da parcela cheia: ano do ultimo exercicio, ou None."""
    ok = [all(c) for c in condicoes(L_, caminho_id, ramo)]
    for i in range(3, 11 - k):
        if all(ok[i:i + k]):
            return i + k
    return None


def conferencias_v33(res):
    print("=" * 78)
    print("CONFERENCIAS v3.3")
    print("=" * 78)
    # (a) a v3.2 e reproduzida pela variante 'v32'
    v32 = {}
    with open(ARQ_V32, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["variante"] == "principal" and r["cenario"] in ("SEM", "NUCLEO", "NUCLEO_GAT"):
                v32[(r["cenario"], r["caminho_rcl"], r["ramo"], int(r["ano"]))] = float(r["estoque_acumulado_real_bi"])
    dif = max(abs(L["estoque"] - v32[(cid, cam, ramo, L["ano"])])
              for (cid, cam, ramo, ext), L_ in res.items() if ext == "v32" and ramo in ("A", "B") for L in L_)
    assert dif < 0.006, dif
    print(f"v3.2 reproduzida pela variante 'v32' (estoque, todos os anos e caminhos): diferenca maxima {dif:.4f} bi")
    # (b) piso
    s = sorted(SERIE_INV_PCT.values())
    media, mediana = sum(s) / len(s), (s[5] if len(s) == 11 else None)
    assert abs(min(s) - 0.0272) < 0.0002 and abs(media - 0.0607) < 0.0005
    print(f"Investimento empenhado/RCL 2015-2025: media {100 * media:.2f}%, mediana {100 * mediana:.2f}%, "
          f"minimo {100 * min(s):.2f}% (2018)")
    print(f"Razao pago no ano/empenhado 2023-2025 = {INV_K:.4f}")
    print("Investimento da LDO (Tab. 39, pago no ano) / RCL da LDO, anos 1-3: "
          + ", ".join(f"{100 * inv_ldo_ratio(t):.2f}%" for t in (1, 2, 3))
          + " -> em empenhado: " + ", ".join(f"{100 * inv_ldo_ratio(t) / INV_K:.2f}%" for t in (1, 2, 3))
          + " -> falta para o piso: " + ", ".join(f"{100 * (PISO_INV - inv_ldo_ratio(t) / INV_K):.2f}" for t in (1, 2, 3))
          + " ponto(s)")
    # (c) Comprev
    print(f"Comprev: recomposicao {COMPREV_RECOMPOSICAO:.2f} bi; aporte do Tesouro ao FFP-MG em 2025 "
          f"{APORTE_FFP_2025:.2f} bi (cabe o credito no ano seguinte); fluxo perdido {COMPREV_FLUXO:.3f} bi/ano "
          f"(2023-2025 nominal: " + ", ".join(f"{v:.3f}" for v in COMPREV_FLUXO_HIST.values()) + ")")
    assert APORTE_FFP_2025 > COMPREV_RECOMPOSICAO
    # (d) DCL
    print(f"DC 2025 {DC_2025:.2f} = Propag {S0:.2f} + precatorios {PREC_DC_2025:.2f} + demais {DEMAIS_DC_2025:.2f}; "
          f"DCL 2025 {DCL_2025:.2f} ({100 * DCL_2025 / RCL_NOM_2025:.2f}% da RCL)")
    print("Demais dividas: amortizacao real anos 1-10 = " + ", ".join(f"{DEMAIS_AMORT[t]:.2f}" for t in ANOS)
          + "; saldo ano 0, 5, 10 = " + ", ".join(f"{DEMAIS_ESTOQUE[t]:.2f}" for t in (0, 5, 10)))
    print("DCL no fim do ano 0: " + "; ".join(f"ramo {r} {DCL_ANO0[r]:.1f} bi" for r in ("A", "B")))
    ldo_dcl = {2027: 185.529523, 2028: 188.880455, 2029: 190.190641}      # Tab. 40 [LDO-I p. 79]
    print("LDO, Tab. 40: DCL/RCL " + ", ".join(f"{100 * ldo_dcl[c] / (LDO[c - 2026]['rcl'] / 1e6):.1f}%" for c in ldo_dcl)
          + " (2027-2029; a DC da LDO, R$ 210,8 bi em 2027, nao separa o abatimento: comparacao so de tendencia)")
    # (e) saldo com a Uniao: unidade
    L_ = res[("SEM", "2,5%", "A", "principal")]
    print(f"Saldo com a Uniao, ramo A, 2,5%: ano 1 {L_[0]['estoque_uniao']:.1f} bi = {pct(L_[0]['estoque_uniao'], L_[0]['rcl']):.1f}% "
          f"da RCL; ano 10 {L_[9]['estoque_uniao']:.1f} bi = {pct(L_[9]['estoque_uniao'], L_[9]['rcl']):.1f}% da RCL (R$ de dez/2025)")


# =============================================================================
# 8. v3.5: CENARIO PRINCIPAL, VARIANTES, CSV E QUADROS DO ANEXO B
# =============================================================================
ARQ_V34 = os.path.join(AQUI, "historico", "cenarios_resultado_v3.4.csv")
ARQ_V35 = os.path.join(AQUI, "historico", "cenarios_resultado_v3.5.csv")
ARQ_V36 = os.path.join(AQUI, "historico", "cenarios_resultado_v3.6.csv")
VENDA = COPASA_REAL                 # dinheiro da venda da companhia de saneamento, a precos de dez/2025
HERANCA = -11.30                    # caixa livre liquido do Executivo em 31/12/2025 (RGF, Anexo 5): fora do saldo; so sensibilidade
SEM_35 = dict(custo_r=JURO_REAL_ESTOQUE)
NUC_35 = dict(NUCLEO, custo_r=JURO_REAL_ESTOQUE, share=SHARE_SEG_ASSIST, tab_prev=PREV_AVAL_2025)
POL_35 = {"SEM": SEM_35, "NUCLEO": NUC_35, "NUCLEO_GAT": NUCLEO_35}
BASE_35 = ("2,5%", "1,9%", "1,0%", "0,0%")
CHOQUES_35 = ("choque 2,5%", "choque 1,9%", "choque 1,0%")
QUEDAS = {"queda 3% ano 3 volta 4": dict(ano=3, queda=-0.03, volta=4), "queda 3% ano 3 sem voltar": dict(ano=3, queda=-0.03, volta=1, perda=0.03),
          "queda 3% ano 6": dict(ano=6, queda=-0.03, volta=2), "queda 3% ano 7": dict(ano=7, queda=-0.03, volta=2), "queda 3% ano 8": dict(ano=8, queda=-0.03, volta=2),
          "queda 5% ano 6": dict(ano=6, queda=-0.05, volta=2), "queda 2% ano 3": dict(ano=3, queda=-0.02, volta=2)}

def prev_deflac(tab, taxa):
    """v3.7: a mesma serie, se contiver correcao monetaria a esta taxa anual, contada do ano 1."""
    return {a: v / (1 + taxa) ** (a - ANO1_CALENDARIO) for a, v in tab.items()}


VAR_35 = {
    "custo_zero": dict(custo_r=0.0), "custo_5_5": dict(custo_r=0.055),
    "venda": dict(fin0=VENDA), "recomposicao_mesmo_ano": dict(recomp_mesmo_ano=True), "venda_recomposicao": dict(fin0=VENDA, recomp_mesmo_ano=True), "venda_no_contador": dict(est0=VENDA),
    "sem_piso_servicos": dict(share=0.0, tab_prev=None), "piso_todos_servicos": dict(share=SHARE_TODOS), "sem_pisos": dict(piso=None, share=0.0, tab_prev=None),
    "safra_2024": dict(tab_prev=PREV_AVAL_2024), "prev_deflac_2": dict(tab_prev=prev_deflac(PREV_AVAL_2025, 0.02)), "prev_deflac_5": dict(tab_prev=prev_deflac(PREV_AVAL_2025, 0.05)), "previdencia_nao_absorvida": dict(share=0.0, tab_prev=None, prev_proj=PREV_AVAL_2025),
    "perimetro_0_5": dict(perim=0.5), "perimetro_1_0": dict(perim=1.0), "heranca_no_contador": dict(est0=HERANCA),
    "gatilho_atrasado": dict(gatilho_lag=2), "gatilho_atrasado_protegido": dict(gatilho_lag=2, gatilho_prov=True), "sem_escape": dict(escape=False, escape_limiar=None), "escape_qualquer_queda": dict(escape=True, escape_limiar=None),
    "piso_fora": dict(piso="fora"), "piso_fora_k1": dict(piso="fora", piso_k=1.0), "prec_leve": dict(prec_extra=PREC_LEVE), "prec_rgf": dict(prec_extra=PREC_RGF),
    "volta_1": dict(volta_anos=1), "volta_2": dict(volta_anos=2), "sem_volta": dict(volta_anos=None), "gatilho_anual": dict(gatilho_modo="anual", volta_anos=None), "recomposicao_sem_devolucao": dict(comprev_modo="saida"),
    "sem_gatilho": dict(gatilho=False), "emenda_atrasa_1": dict(inicio_gat=3), "emenda_atrasa_2": dict(inicio_gat=4), "so_executivo_80": dict(adesao=0.80), "so_executivo_58_5": dict(adesao=0.585), "gatilho_metade": dict(alpha_gat=0.35),
    "sem_custeio": dict(f06=0.0), "custeio_metade": dict(f06=0.05), "sem_revisao": dict(s12=0.0), "sem_custeio_revisao": dict(f06=0.0, s12=0.0), "sem_gatilho_custeio_revisao": dict(gatilho=False, f06=0.0, s12=0.0),
}


def prepara_35():
    CAMINHOS["1,9%"] = (0.019, False)
    CAMINHOS["choque 1,9%"] = (0.019, True)
    for nome, ch in QUEDAS.items():
        for g, rot in ((0.025, "2,5%"), (0.019, "1,9%")):
            CAMINHOS[f"{nome} | {rot}"] = (g, ch)


def roda_todos_35():
    prepara_35()
    res = {}
    for cam in BASE_35 + CHOQUES_35:
        for ramo in ("A", "B"):
            for pid, kw in POL_35.items():
                res[(pid, cam, ramo, "principal")] = roda(cam, ramo, **kw)
                for rf in ("zero", "ldo"):
                    res[(pid, cam, ramo, "recfin_" + rf)] = roda(cam, ramo, recfin=rf, **kw)
            for var, aj in VAR_35.items():
                res[("NUCLEO_GAT", cam, ramo, var)] = roda(cam, ramo, **dict(NUCLEO_35, **aj))
        for pid in ("NUCLEO", "NUCLEO_GAT"):
            res[(pid, cam, "A30", "principal")] = roda(cam, "A30", **POL_35[pid])
    for cam in BASE_35:
        for ramo in ("A", "B"):
            res[("M02_70", cam, ramo, "principal")] = roda(cam, ramo, alpha=0.70)
            res[("M02_70", cam, ramo, "so_minimos")] = roda(cam, ramo, alpha=0.70, excl=PARTE_MINIMOS)
            res[("M06_10", cam, ramo, "principal")] = roda(cam, ramo, f06=0.10)
            res[("M12_05", cam, ramo, "principal")] = roda(cam, ramo, s12=0.05)
            res[("SEM", cam, ramo, "bruto")] = roda(cam, ramo, liquido=False, **SEM_35)
    for nome in QUEDAS:
        for rot in ("2,5%", "1,9%"):
            cam = f"{nome} | {rot}"
            for ramo in ("A", "B"):
                res[("NUCLEO_GAT", cam, ramo, "principal")] = roda(cam, ramo, **NUCLEO_35)
                res[("NUCLEO_GAT", cam, ramo, "sem_escape")] = roda(cam, ramo, **dict(NUCLEO_35, escape=False, escape_limiar=None))
                res[("NUCLEO_GAT", cam, ramo, "escape_qualquer_queda")] = roda(cam, ramo, **dict(NUCLEO_35, escape=True, escape_limiar=None))
    return res


COLS_35 = ["cenario", "variante", "caminho_rcl", "ramo", "ano", "ano_calendario", "rcl_real_bi",
           "parcela_uniao_pct", "demais_dividas_pct", "servico_divida_pct", "fef_exigido_pct", "investimento_exigido_pct",
           "compensacao_pct", "aplicacoes_fora_do_primario_pct", "investimento_acima_da_LDO_pct",
           "receitas_financeiras_pct", "primario_referencia_pct", "efeito_M02_M10_pct", "efeito_M06_pct",
           "efeito_M12_liquido_pct", "receita_cedida_pct", "recomposicao_comprev_pct", "primario_pct",
           "cobertura_anual_pct", "encargo_real_bi", "piso_servicos_real_bi", "estoque_acumulado_pct", "estoque_acumulado_real_bi",
           "estoque_uniao_pct", "gatilho_ligado", "investimento_total_pct", "piso_extra_pct", "precatorios_extra_pct",
           "dcl_pct", "dcl_real_bi", "estoque_uniao_real_bi"]


def grava_csv_35(res):
    with open(ARQ_SAIDA, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(COLS_35)
        n = 0
        for (cid, cam, ramo, extra), linhas in res.items():
            for L in linhas:
                r = L["rcl"]
                w.writerow([cid, extra, cam, ramo, L["ano"], L["cal"], f"{r:.2f}",
                            *(f"{pct(L[k], r):.2f}" for k in (
                                "parcela", "outras", "serv", "fef", "inv", "comp", "aplic", "inv_extra", "recfin",
                                "prim_ref", "m02", "m06", "m12", "cedido", "comprev", "prim", "cob")),
                            f"{L['enc']:.2f}", f"{L['extra_serv']:.2f}", f"{pct(L['estoque'], r):.2f}", f"{L['estoque']:.2f}",
                            f"{pct(L['estoque_uniao'], r):.1f}", "sim" if L["gatilho"] else "não",
                            *(f"{pct(L[k], r):.2f}" for k in ("inv_total", "piso_extra", "prec")),
                            f"{pct(L['dcl'], r):.1f}", f"{L['dcl']:.2f}", f"{L['estoque_uniao']:.2f}"])
                n += 1
    return n


def conferencias_35(res):
    """Antes de usar os resultados: a v3.4 e reproduzida com os parametros em branco; a v3.5, sem a escape; o saldo fecha; o gatilho so fica desligado com saldo negativo no ano da escape."""
    pub = {}
    with open(ARQ_V34, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pub[(r["cenario"], r["caminho_rcl"], r["ramo"], r["variante"], int(r["ano"]))] = float(r["estoque_acumulado_real_bi"])
    res34 = roda_todos()
    conferencias_v33(res34)
    dif, n = 0.0, 0
    for (cid, cam, ramo, ext), L_ in res34.items():
        for L in L_:
            k = (cid, cam, ramo, ext, L["ano"])
            if k in pub:
                dif = max(dif, abs(L["estoque"] - pub[k]))
                n += 1
    assert n == len(pub) and dif < 0.006, (n, len(pub), dif)
    print(f"v3.4 reproduzida com os parametros em branco: {n} linhas, diferenca maxima {dif:.4f} bi")
    res.update(roda_todos_35())
    a = g = 0
    for (cid, cam, ramo, ext), L_ in res.items():
        if cid not in POL_35 or ext != "principal":
            continue
        prev = 0.0
        for i, L in enumerate(L_):
            assert abs(L["est_ini"] - prev) < 1e-9 and abs(L["estoque"] - (L["est_ini"] - L["enc"] + L["cob"])) < 1e-9
            prev = L["estoque"]
            a += 1
            if cid == "NUCLEO_GAT" and i >= 2 and L_[i - 1]["estoque"] < -1e-9:
                assert L["gatilho"] or L["escape"]
                g += 1
    pub35, n35, dif35 = {}, 0, 0.0
    with open(ARQ_V35, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pub35[(r["cenario"], r["caminho_rcl"], r["ramo"], r["variante"], int(r["ano"]))] = float(r["estoque_acumulado_real_bi"])
    for (cid, cam, ramo, ext), L_ in res.items():
        if ext == "sem_escape":
            chave = (cid, cam, ramo, "principal")                       # v3.6: sem escape = principal da v3.5
        elif ext in ("gatilho_atrasado_protegido",):
            continue
        else:
            choque_ = cam.startswith(("choque", "queda"))
            if choque_ and ext != "escape_qualquer_queda" and cid == "NUCLEO_GAT" and ext != "sem_gatilho":
                continue                                                # com a escape, os caminhos de queda mudam de proposito
            chave = (cid, cam, ramo, ext)
        for L in L_:
            k = (*chave, L["ano"])
            if k in pub35:
                dif35 = max(dif35, abs(L["estoque"] - pub35[k]))
                n35 += 1
    assert dif35 < 0.006, (n35, dif35)
    print(f"v3.5 reproduzida fora dos caminhos de queda, e neles sem a escape: {n35} linhas, diferenca maxima {dif35:.4f} bi")
    pub36, dif36, n36 = {}, 0.0, 0
    with open(ARQ_V36, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pub36[(r["cenario"], r["caminho_rcl"], r["ramo"], r["variante"], int(r["ano"]))] = float(r["estoque_acumulado_real_bi"])
    for (cid, cam, ramo, ext), L_ in res.items():
        for L in L_:
            k = (cid, cam, ramo, ext, L["ano"])
            if k in pub36:
                dif36 = max(dif36, abs(L["estoque"] - pub36[k]))
                n36 += 1
    assert n36 == len(pub36) and dif36 < 0.006, (n36, len(pub36), dif36)
    print(f"v3.6 reproduzida: {n36} linhas, diferenca maxima {dif36:.4f} bi")
    print(f"saldo inicial - encargo + cobertura = saldo final: {a} anos-caso; gatilho ligado com saldo negativo: {g} anos-caso")
    print(f"encargo real do cenario principal: {100 * JURO_REAL_ESTOQUE:.2f}% ao ano; venda: R$ {VENDA:.2f} bi; parte protegida: {100 * SHARE_SEG_ASSIST:.1f}%")


def quita(L_):
    neg = [x["ano"] for x in L_ if x["estoque"] < -1e-9]
    return (neg[-1] + 1 if neg[-1] < 10 else None) if neg else 1


def acaba(L_):
    ok = [x["cob"] >= -1e-9 for x in L_]
    for i in range(10):
        if all(ok[i:]):
            ex = [k + 1 for k in range(i) if ok[k]]
            return f"a partir do ano {i + 1}" + (f" (e no ano {ex[0]})" if ex else "")
    ex = [k + 1 for k in range(10) if ok[k]]
    return f"não (só sobra o ano {ex[0]})" if ex else "não"


def brn(v, c=1):
    s = f"{v:.{c}f}".replace(".", ",").replace("-", "−")
    return "0,0" if s == "−0,0" else s


def quadros_35(res):
    """Quadros B.2, B.3, B.4, B.6 e B.7 do Anexo B, em markdown."""
    def R(cid, cam, ramo, extra="principal"):
        return res[(cid, cam, ramo, extra)]

    NOME = {"2,5%": "2,5%", "1,9%": "1,9%", "1,0%": "1,0%", "0,0%": "Zero"}
    POL = (("SEM", "Sem medidas"), ("NUCLEO", "Núcleo"), ("NUCLEO_GAT", "Núcleo + gatilho"))
    o = {}
    b2 = ["| Crescimento real | Política | Com abatimento (% da RCL) | Com abatimento (R$ bi) | Sem abatimento (% da RCL) | Sem abatimento (R$ bi) |", "|---|---|---:|---:|---:|---:|"]
    for cam in BASE_35:
        for pid, nm in POL:
            a, c = R(pid, cam, "A")[-1], R(pid, cam, "B")[-1]
            b2.append(f"| {NOME[cam]} | {nm} | {brn(pct(a['estoque'], a['rcl']))} | {brn(a['estoque'])} | {brn(pct(c['estoque'], c['rcl']))} | {brn(c['estoque'])} |")
    o["B2"] = "\n".join(b2)
    b3 = ["| Crescimento real | Política | Com abatimento: insuficiência anual acaba | Com abatimento: estoque é pago | Com abatimento: declaração | Sem abatimento: insuficiência anual acaba | Sem abatimento: estoque é pago | Sem abatimento: declaração |", "|---|---|---|---|---|---|---|---|"]
    for cam in BASE_35:
        for pid, nm in POL:
            cel = []
            for ramo in ("A", "B"):
                L_ = R(pid, cam, ramo)
                q, d = quita(L_), declaracao_k(L_, cam, ramo, 3)
                cel += [acaba(L_), f"no ano {q}" if q else "não", f"ano {d}" if d else "fora do horizonte"]
            b3.append(f"| {NOME[cam]} | {nm} | " + " | ".join(cel) + " |")
    o["B3"] = "\n".join(b3)
    lin = []

    def peca(nome, f):
        lin.append(f"| {nome} | " + " | ".join(brn(f(c)) for c in BASE_35) + " |")

    def ganho(pid, ramo, ext="principal"):
        return lambda c: sum(R(pid, c, ramo, ext)[i]["prim"] - R("SEM", c, ramo)[i]["prim"] for i in range(10))

    peca("Abatimento líquido (com menos sem abatimento)", lambda c: sum(R("SEM", c, "A")[i]["cob"] - R("SEM", c, "B")[i]["cob"] for i in range(10)))
    peca("Abatimento bruto (sem descontar cessões e recomposição)", lambda c: sum(R("SEM", c, "A", "bruto")[i]["cob"] - R("SEM", c, "B")[i]["cob"] for i in range(10)))
    peca("Limite de despesa (70%, com as exclusões legais)", ganho("M02_70", "A"))
    peca("Custeio dos militares (10% da diferença)", ganho("M06_10", "A"))
    peca("Revisão da renúncia (5%, parte livre)", ganho("M12_05", "A"))
    peca("Núcleo, em conjunto, com abatimento", ganho("NUCLEO", "A"))
    peca("Núcleo, em conjunto, sem abatimento", ganho("NUCLEO", "B"))
    peca("Núcleo + gatilho, com abatimento", ganho("NUCLEO_GAT", "A"))
    peca("Núcleo + gatilho, sem abatimento", ganho("NUCLEO_GAT", "B"))
    peca("Custo do piso dos serviços, com gatilho e abatimento", lambda c: sum(x["extra_serv"] for x in R("NUCLEO_GAT", c, "A")))
    peca("Custo do piso dos serviços, com gatilho, sem abatimento", lambda c: sum(x["extra_serv"] for x in R("NUCLEO_GAT", c, "B")))
    peca("Encargo somado, com gatilho e abatimento", lambda c: sum(x["enc"] for x in R("NUCLEO_GAT", c, "A")))
    peca("Encargo somado, com gatilho, sem abatimento", lambda c: sum(x["enc"] for x in R("NUCLEO_GAT", c, "B")))
    o["B4"] = "\n".join(["| Peça | Crescimento de 2,5% | Crescimento de 1,9% | Crescimento de 1,0% | Crescimento zero |", "|---|---:|---:|---:|---:|"] + lin)

    def tripla(cam, ramo, var):
        L_ = R("NUCLEO_GAT", cam, ramo, var)
        q, d = quita(L_), declaracao_k(L_, cam, ramo, 3)
        return f"{q or 'não paga'} / {d or 'fora'} / {brn(L_[-1]['estoque'])}"

    b6 = ["| Caso | Sem custo | 5,5% ao ano | 8,25% ao ano (principal) |", "|---|---|---|---|"]
    for cam, nm in (("2,5%", "2,5%"), ("1,9%", "1,9%"), ("1,0%", "1,0%"), ("0,0%", "Zero"), ("choque 2,5%", "Choque sobre 2,5%"), ("choque 1,9%", "Choque sobre 1,9%")):
        for ramo, rt in (("A", "com abatimento"), ("B", "sem abatimento")):
            b6.append(f"| {nm}, {rt} | {tripla(cam, ramo, 'custo_zero')} | {tripla(cam, ramo, 'custo_5_5')} | {tripla(cam, ramo, 'principal')} |")
    o["B6"] = "\n".join(b6)
    b7 = ["| Crescimento real | Com abatimento: sem medidas | Com abatimento: núcleo + gatilho | Sem abatimento: sem medidas | Sem abatimento: núcleo + gatilho |", "|---|---|---|---|---|"]
    for cam, nm in (("2,5%", "2,5%"), ("1,9%", "1,9%"), ("1,0%", "1,0%"), ("0,0%", "Zero"), ("choque 2,5%", "Choque sobre 2,5%"), ("choque 1,9%", "Choque sobre 1,9%"), ("choque 1,0%", "Choque sobre 1%")):
        cel = []
        for pid, ramo in (("SEM", "A"), ("NUCLEO_GAT", "A"), ("SEM", "B"), ("NUCLEO_GAT", "B")):
            x = R(pid, cam, ramo)[-1]
            cel.append(f"{brn(dcl0_pct(cam, ramo), 0)} → {brn(pct(x['dcl'], x['rcl']), 0)}")
        b7.append(f"| {nm} | " + " | ".join(cel) + " |")
    o["B7"] = "\n".join(b7)
    return o


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # os quadros trazem sinais que a saida em arquivo nem sempre aceita
    conferencias()
    resultados = {}
    conferencias_35(resultados)
    n_linhas = grava_csv_35(resultados)
    for nome, md in quadros_35(resultados).items():
        print(f"\n### Quadro {nome[0]}.{nome[1:]}\n\n{md}")
    print(f"\nCSV gravado em: {ARQ_SAIDA} ({n_linhas} linhas)")
