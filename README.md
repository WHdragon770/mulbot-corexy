# Mulbot CoreXY 200³

Versão CoreXY da impressora 3D **Mulbot DL1** (3D Printing World), quase toda impressa:
quadro oco com passagem de cabos, guias em V impressas no X, Y e Z (roldana de resina com 10 roletes impressos junto),
extrusora direta, presilha do vidro em botão excêntrico, parafusos M10/M6 impressos, **esteira porta-cabos impressa** no X e no Y.
**Nada precisa de suporte de impressão** (paredes até 45°, pontes até 10 mm). Área de impressão 200 × 200 × 200 mm.

## Pastas

| Pasta | O que tem |
|---|---|
| `entrega/02 STL para imprimir` | todas as peças, separadas por conjunto, com a quantidade no nome + `lista_de_impressao.csv` |
| `entrega/03 Desenhos de montagem` | 12 folhas A4 (PNG 300 dpi + PDF): capa, quadro, eixos, mesa, correias, eletrônica, roldana V, ligação, passagem de cabos, esteira porta-cabos |
| `entrega/04 Detalhes (imagens)` | closes da esteira porta-cabos (elo, esteira X, esteira Y, entrada do cabo na torre) |
| `entrega/render` | renders da montagem |
| `entrega/video` | prévia do vídeo de montagem (rascunho rápido, **versão antiga**, antes da esteira e do reprojeto sem suporte) |
| `final/corexy_montagem_leve.blend` | montagem 3D inteira (malhas leves) — base do vídeo |
| `scripts/` | gerador paramétrico da CoreXY (`cxy.py`), passagem de cabos, STL, desenhos (`desenhos/`), vídeo (`video/`) |
| `scripts_mulbot/` | scripts auxiliares da montagem da Mulbot original (dependência de `cxy.py`) |
| `out/` | dados que o vídeo usa (posições das peças, poses da máquina funcionando, peso de cada quadro) |

## Versão atual (21/10/2026)

- **Sem suporte**: todas as peças novas foram redesenhadas pra imprimir sem suporte, na orientação fixa de
  `scripts/placas/impressao_rot.json` (furo deitado vira gota, cavidade com teto em 2 águas). Não girar as peças no fatiador.
- **Esteira porta-cabos** (`scripts/esteira.py`, folha CXY-11): esteira X atrás da viga X (11 elos) e esteira Y por fora
  do lado direito (12 elos), o mesmo elo impresso em pé, pino de filamento 1,75 mm. O cabo da cabeça entra no quadro pela
  parede de fora da torre de trás direita. `ESTEIRA=0` volta o cabo solto (umbilical) da versão anterior.
- Os elos mudam de forma em cada pose: a colisão deles é conferida à parte por `scripts/colisao_esteira.py` (0 interferências em 22 poses).

## Renderizar o vídeo

Leia **[RENDER_INSTRUCOES.txt](RENDER_INSTRUCOES.txt)** — começando pela seção 0 (o que mudou na máquina e o que refazer antes de renderizar). Tem tudo: o que instalar (Blender 4.2.3), o comando,
quanto tempo leva (≈13 h em CPU, < 1 h com GPU via `CYCLES_DEVICE=OPTIX`), como retomar se cair e o checklist do resultado.

Resumo: `./scripts/video/render_noite.sh "" cycles` → `final/video/corexy_video_cycles.mp4`

## Regerar a geometria (opcional)

`scripts/cxy.py` regera a montagem inteira, mas precisa dos modelos originais da Mulbot DL1 (repositório público da
3D Printing World) e do ambiente usado aqui (`~/mulbot`). Para só renderizar o vídeo isso **não** é necessário.
