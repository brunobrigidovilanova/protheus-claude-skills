# -*- coding: utf-8 -*-
"""Primitivas para desenhar os fluxogramas que entram na MIT044.

Nao e um gerador automatico: e a caixa de ferramentas para escrever, por
documento, um script curto que descreve os diagramas daquela customizacao. O
resultado sai em PNG e entra no .docx pelo item {"tipo": "figura"} do JSON.

Uso tipico (um arquivo por documento, ao lado do JSON de conteudo):

    import sys, os
    sys.path.insert(0, os.path.expanduser(
        r'~/.claude/skills/mit044-especificacao/scripts'))
    from fluxograma import *

    f, ax = figura(4.2)
    caixa(ax, 50, 80, 50, 10, 'Usuário importa a planilha')
    losango(ax, 50, 55, 44, 14, 'Validação\\naprovada?')
    caixa(ax, 50, 30, 50, 10, 'Grava os itens', bc=VERDE_B, fc=VERDE_F)
    seta(ax, (50, 75), (50, 62))
    seta(ax, (50, 48), (50, 35))
    salva(f, 'fluxo-1-importacao.png')

Convencoes que fazem o desenho sair legivel no Word:

- O eixo vai de 0 a 100 nos dois sentidos, sempre. So a altura da figura muda.
- A largura nasce em 6,3 pol - a mancha da pagina A4 do template. Como a imagem
  entra no documento nesse mesmo tamanho, nao ha reducao: o corpo de letra que
  voce escolhe aqui e o que o leitor ve.
- Texto de caixa entre 7,5 e 8,5 pt; rotulo de seta, 7 pt. Menor que isso nao
  sobrevive a impressao.
- Antes de fechar, confira sobreposicao: rotulo de seta encostando em caixa e o
  defeito mais comum, e so aparece olhando o PNG pronto.
- A paleta abaixo foi escolhida para continuar legivel impressa em preto e
  branco: cada cor tem luminosidade diferente das outras.

Requer matplotlib (pip install matplotlib).
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

__all__ = ['figura', 'caixa', 'losango', 'seta', 'caminho', 'rotulo', 'faixa',
           'salva', 'LARGURA_POL', 'AZUL_B', 'AZUL_F', 'CINZA_B', 'CINZA_F',
           'VERDE_B', 'VERDE_F', 'VERM_B', 'VERM_F', 'AMAR_B', 'AMAR_F', 'TXT']

LARGURA_POL = 6.3        # mancha da pagina A4 do template, em polegadas
SAIDA_PADRAO = 'figuras'

AZUL_B, AZUL_F = '#1F3864', '#DCE6F1'    # fluxo normal
CINZA_B, CINZA_F = '#595959', '#F2F2F2'  # o que o sistema faz sozinho
VERDE_B, VERDE_F = '#3F6E2A', '#E2EFDA'  # conclusao com sucesso
VERM_B, VERM_F = '#953735', '#FBE4E4'    # recusa, erro, cancelamento
AMAR_B, AMAR_F = '#9C6500', '#FFF2CC'    # decisao e pendencia
TXT = '#1A1A1A'

plt.rcParams['font.family'] = 'DejaVu Sans'


def figura(altura, largura=LARGURA_POL):
    """Cria a area de desenho com eixo 0..100 e sem margens."""
    f, ax = plt.subplots(figsize=(largura, altura))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    f.subplots_adjust(left=0.004, right=0.996, top=0.996, bottom=0.004)
    return f, ax


def caixa(ax, x, y, w, h, texto, bc=AZUL_B, fc=AZUL_F, fs=8.5, negrito=False):
    """Retangulo de cantos arredondados centrado em (x, y)."""
    ax.add_patch(FancyBboxPatch((x - w / 2., y - h / 2.), w, h,
                                boxstyle='round,pad=0,rounding_size=1.6',
                                linewidth=1.05, edgecolor=bc, facecolor=fc, zorder=2))
    ax.text(x, y, texto, ha='center', va='center', fontsize=fs, color=TXT, zorder=3,
            fontweight='bold' if negrito else 'normal', linespacing=1.35)


def losango(ax, x, y, w, h, texto, bc=AMAR_B, fc=AMAR_F, fs=8.5):
    """Decisao. Cabe pouco texto: duas linhas curtas, o resto vai em rotulo."""
    ax.add_patch(Polygon([(x, y + h / 2.), (x + w / 2., y), (x, y - h / 2.),
                          (x - w / 2., y)], closed=True, linewidth=1.05,
                         edgecolor=bc, facecolor=fc, zorder=2))
    ax.text(x, y, texto, ha='center', va='center', fontsize=fs, color=TXT,
            linespacing=1.3, zorder=3)


def seta(ax, p1, p2, cor=CINZA_B, lw=1.15, curva=0.0, tracejada=False, ponta=True):
    """Liga dois pontos. `curva` positiva arqueia para um lado, negativa para o outro;
    tracejada marca o que acontece em outra execucao (retomada, retorno a fila)."""
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle='-|>' if ponta else '-',
                                 mutation_scale=10, linewidth=lw, color=cor,
                                 shrinkA=0, shrinkB=0, zorder=1,
                                 linestyle='--' if tracejada else '-',
                                 connectionstyle='arc3,rad=%s' % curva))


def caminho(ax, pontos, cor=CINZA_B, lw=1.15, tracejada=False):
    """Ligacao em L ou em U: segmentos retos, com a ponta no ultimo trecho.

    Preferivel a uma curva larga quando o desvio teria de cruzar outras caixas.
    """
    for i in range(len(pontos) - 1):
        seta(ax, pontos[i], pontos[i + 1], cor=cor, lw=lw, tracejada=tracejada,
             ponta=(i == len(pontos) - 2))


def rotulo(ax, x, y, t, fs=7.6, cor=CINZA_B, ha='center', negrito=False):
    """Texto solto: 'sim', 'não', a condicao de um desvio, uma nota curta."""
    ax.text(x, y, t, ha=ha, va='center', fontsize=fs, color=cor, linespacing=1.3,
            zorder=3, fontweight='bold' if negrito else 'normal')


def faixa(ax, x, y, w, h, titulo, fc='#F6F9FD', bc='#C6D3E6'):
    """Agrupador ao fundo - raia de responsavel, etapa ou quadro lateral."""
    ax.add_patch(Rectangle((x, y), w, h, linewidth=1.0, edgecolor=bc,
                           facecolor=fc, zorder=0))
    ax.text(x + w / 2., y + h - 5.0, titulo, ha='center', va='center',
            fontsize=8.8, fontweight='bold', color=AZUL_B, linespacing=1.3, zorder=1)


def salva(f, nome, pasta=SAIDA_PADRAO, dpi=230):
    """Grava o PNG e fecha a figura. Devolve o caminho gravado."""
    os.makedirs(pasta, exist_ok=True)
    caminho_png = os.path.join(pasta, nome)
    f.savefig(caminho_png, dpi=dpi, facecolor='white')
    plt.close(f)
    print('gerado', caminho_png)
    return caminho_png
