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
| `entrega/07 Mesa aquecida (opcional)` | mesa aquecida em 2 opções (220×220 12 V e 235×235 24 V): peças que mudam, imagens, `.glb`, LEIA-ME com links e firmware |
| `entrega/04 Detalhes (imagens)` | closes da esteira porta-cabos (elo, esteira X, esteira Y, entrada do cabo na torre) |
| `entrega/render` | renders da montagem + vídeo de montagem renderizado (versão de 20/10, antes da esteira) |
| `entrega/video` | prévia do vídeo de montagem (rascunho rápido, **versão antiga**, antes da esteira e do reprojeto sem suporte) |
| `final/corexy_celular.glb` | **versão pra celular** (13,7 MB, ~900 mil triângulos, tamanho real em metros): abre em qualquer visualizador 3D/AR do celular. Gerada por `scripts/glb_celular.py` |
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

## Mesa aquecida (opcional, 21/10/2026)

`MESA=220` (placa de alumínio 220×220×3 12 V, recomendada) ou `MESA=235` (235×235×3 24 V, mesa da Ender 3) antes do `cxy.py`;
sem `MESA` a máquina continua como antes. Scripts: `scripts/mesa_aquecida.py` e `scripts/fonte_maior.py`.
- A placa fica entre o localizador e o vidro; o topo do vidro continua no mesmo lugar e o resto da mesa desce 3 mm.
- Localizador novo (bordas 3 mm mais altas; na 220 com calço em L), presilha com pescoço 3 mm maior, calço de 3 mm no fim de curso Z.
- Fonte de 360 W (12 V 30 A ou 24 V 15 A, 215×115×50) com proteção nova impressa (IEC em pé) e módulo MOSFET da mesa.
- Conferido: sem colisão (mesa em 0/100/200), peças novas sem suporte (0 ilhas, ponte 10). `scripts/checa_mesa.py` confere a mesa.

## Renderizar o vídeo

Leia **[RENDER_INSTRUCOES.txt](RENDER_INSTRUCOES.txt)** — começando pela seção 0 (o que mudou na máquina e o que refazer antes de renderizar). Tem tudo: o que instalar (Blender 4.2.3), o comando,
quanto tempo leva (≈13 h em CPU, < 1 h com GPU via `CYCLES_DEVICE=OPTIX`), como retomar se cair e o checklist do resultado.

Resumo: `./scripts/video/render_noite.sh "" cycles` → `final/video/corexy_video_cycles.mp4`

## Regerar a geometria (opcional)

`scripts/cxy.py` regera a montagem inteira, mas precisa dos modelos originais da Mulbot DL1 (repositório público da
3D Printing World) e do ambiente usado aqui (`~/mulbot`). Para só renderizar o vídeo isso **não** é necessário.
