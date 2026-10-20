# Mulbot CoreXY 200³

Versão CoreXY da impressora 3D **Mulbot DL1** (3D Printing World), quase toda impressa:
quadro oco com passagem de cabos, guias em V impressas no X, Y e Z (roldana de resina com 10 roletes impressos junto),
extrusora direta, presilha do vidro em botão excêntrico, parafusos M10/M6 impressos. Área de impressão 200 × 200 × 200 mm.

## Pastas

| Pasta | O que tem |
|---|---|
| `entrega/02 STL para imprimir` | todas as peças, separadas por conjunto, com a quantidade no nome + `lista_de_impressao.csv` |
| `entrega/03 Desenhos de montagem` | 11 folhas A4 (PNG 300 dpi + PDF): capa, quadro, eixos, mesa, correias, eletrônica, roldana V, ligação, passagem de cabos |
| `entrega/render` | renders da montagem |
| `entrega/video` | prévia do vídeo de montagem (rascunho rápido) |
| `final/corexy_montagem_leve.blend` | montagem 3D inteira (malhas leves) — base do vídeo |
| `scripts/` | gerador paramétrico da CoreXY (`cxy.py`), passagem de cabos, STL, desenhos (`desenhos/`), vídeo (`video/`) |
| `scripts_mulbot/` | scripts auxiliares da montagem da Mulbot original (dependência de `cxy.py`) |
| `out/` | dados que o vídeo usa (posições das peças, poses da máquina funcionando, peso de cada quadro) |

## Renderizar o vídeo

Leia **[RENDER_INSTRUCOES.txt](RENDER_INSTRUCOES.txt)** — tem tudo: o que instalar (Blender 4.2.3), o comando,
quanto tempo leva (≈13 h em CPU, < 1 h com GPU via `CYCLES_DEVICE=OPTIX`), como retomar se cair e o checklist do resultado.

Resumo: `./scripts/video/render_noite.sh "" cycles` → `final/video/corexy_video_cycles.mp4`

## Regerar a geometria (opcional)

`scripts/cxy.py` regera a montagem inteira, mas precisa dos modelos originais da Mulbot DL1 (repositório público da
3D Printing World) e do ambiente usado aqui (`~/mulbot`). Para só renderizar o vídeo isso **não** é necessário.
