# A conta que não fecha — pacote dos cenários

Este pacote refaz os cenários de dez anos do livro *A conta que não fecha: causas da crise fiscal de Minas Gerais e um plano para sair dela*, de Cláudio Ribeiro Figueiredo (1ª edição, 2026). As premissas, o método e os quadros estão no Anexo B do livro; aqui está a máquina que gera aqueles números.

## O que tem aqui

| Arquivo | O que é |
|---|---|
| `modelo_cenarios.py` | O modelo, versão 3.7. Python 3, só biblioteca padrão. Cada premissa está no código, com fonte e natureza (dado oficial, cálculo ou hipótese declarada). |
| `entradas/IBGE_SIDRA_t1737_IPCA_numero-indice_consulta_2026-10-18.json` | IPCA, número-índice mensal (IBGE, SIDRA, tabela 1737), consulta de 18/10/2026. |
| `entradas/series-financas-mg-reais-ipca-dez2025.csv` | Séries fiscais de Minas Gerais, em valores nominais e a preços de dezembro de 2025 (SICONFI: RREO e RGF). Cada linha traz o endereço da consulta à API do Tesouro Nacional. |
| `historico/cenarios_resultado_v3.2.csv`, `v3.4`, `v3.5` e `v3.6` | Resultados das versões anteriores. As conferências exigem que o modelo os reproduza: as versões 3.2 e 3.4 com os parâmetros novos em branco, a 3.5 sem a cláusula de escape, a 3.6 em todas as linhas. |
| `cenarios_resultado.csv` | Resultados da versão 3.7, 8.240 linhas: os números do livro. |

## Como rodar

```
python modelo_cenarios.py
```

Na pasta do script, sem mudar a estrutura de pastas. Antes de calcular, o script confere as próprias entradas e para se uma conferência falhar: as metas em caixa batem com o quadro do serviço da dívida da LDO 2027; a prestação reproduz as parcelas já pagas; a conta gráfica sem o abatimento chega a R$ 12,14 bi; os parâmetros novos em branco reproduzem as versões 3.2 e 3.4, e, sem a cláusula de escape, o modelo reproduz a 3.5; a 3.6 é reproduzida em todas as linhas; a série do investimento empenhado bate com a do Capítulo 19; a dívida consolidada inicial bate com o relatório fiscal; o saldo fecha em cada ano; e o gatilho só fica desligado com saldo negativo no ano da cláusula de escape. Depois, mostra os quadros no terminal e regrava `cenarios_resultado.csv`, que deve sair idêntico ao publicado.

## O arquivo de resultados

Cada linha combina cenário de política (`cenario`), variante de sensibilidade (`variante`), caminho de crescimento da receita (`caminho_rcl`), tratamento do abatimento com ativos (`ramo`: A com abatimento, B sem, A30 com abatimento de 30%) e ano (1 a 10; o ano 1 é 2027). As colunas trazem os componentes da conta em proporção da receita corrente líquida, a cobertura anual, o encargo e o custo do piso dos serviços em reais, a insuficiência acumulada (em proporção da receita e em reais), se o gatilho estava ligado, o investimento total, o custo do piso de investimento, os precatórios a mais e a dívida consolidada líquida. O cenário principal leva o encargo de 8,25% reais dentro do saldo, o piso de segurança ativa e assistência e a avaliação atuarial de 31/12/2025.

## O que o modelo é

Aritmética sobre metas oficiais e regras do programa federal de renegociação, com premissas declaradas. **Não é previsão.** Mostra a ordem de grandeza do problema, o peso de cada escolha e onde a conta deixa de fechar. O que ele não faz está listado no Anexo B do livro ("O que o modelo não faz"); entre outras coisas, estima o custo de uma proteção selecionada de serviços sob regra proporcional, mas não mede a entrega nem protege todos os serviços, e trata a previdência civil pelo primário fixo em proporção da receita, com duas sensibilidades para ela.

Para outra LDO ou outra data de adoção, trocam-se as metas, o serviço da dívida, o investimento projetado e a constante que fixa o ano 1 no calendário (`ANO1_CALENDARIO`), e revê-se o fator da transição tributária, que segue datas fixas.

## Versão

A marca `1a-edicao` identifica os arquivos que geraram os números da 1ª edição do livro. Correções futuras ganham marca nova; a da 1ª edição não muda.

## Licença

Código sob a licença MIT (arquivo `LICENSE`). Os dados de entrada são públicos (IBGE e Tesouro Nacional). Resultados e documentação sob CC BY 4.0, com citação do livro.

## Como citar

FIGUEIREDO, Cláudio Ribeiro. *A conta que não fecha: causas da crise fiscal de Minas Gerais e um plano para sair dela*. 1. ed. 2026. Pacote dos cenários, versão 3.7 (marca `1a-edicao`).
