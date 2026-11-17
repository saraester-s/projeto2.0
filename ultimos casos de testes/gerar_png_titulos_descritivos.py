"""PNGs com título na figura e no nome do arquivo (o nome diz o que é)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from gerar_custo_tempo_ordem import ORDEM, pack
from gerar_relatorio_pdf import C1, C2, C3, C4, br, floats, load, stats, style

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "figuras" / "png-com-titulo"
DPI = 300

LABS = [
    "Com segurança\nadulteração\nfalha",
    "Com segurança\nsem adulteração\nsucesso",
    "Sem segurança\nadulteração\nsucesso",
    "Sem segurança\nsem adulteração\nsucesso",
]


def save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.25, facecolor="white")
    plt.close(fig)
    print(path.name)


def table_png(title, headers, rows, name, col_widths=None, figsize=(12.0, 3.4)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    ax.set_title(title, fontsize=13, pad=12, loc="center", color="#111827", fontweight="bold")
    table = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.85)
    if col_widths:
        for i, w in enumerate(col_widths):
            for r in range(len(rows) + 1):
                table[(r, i)].set_width(w)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#E5E7EB")
        if r == 0:
            cell.set_facecolor("#111827")
            cell.set_text_props(color="white", weight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#F9FAFB")
    save(fig, name)


def main() -> None:
    style()
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 13, "axes.labelsize": 10})
    if OUT.exists():
        for p in OUT.glob("*.png"):
            p.unlink()

    series = [pack(item) for item in ORDEM]
    cores = [s["cor"] for s in series]
    xs = np.arange(4)

    # 1. matriz
    fig, ax = plt.subplots(figsize=(8.6, 3.1))
    ax.axis("off")
    ax.set_title("Matriz experimental: allowlist × adulteração do firmware", fontsize=13, pad=10, fontweight="bold")
    matrix = [
        ["", "Firmware limpo", "Firmware adulterado"],
        ["Com segurança\nPOST /atestar", "sucesso · HTTP 200", "falha · HTTP 403"],
        ["Sem segurança\nPOST /leitura", "sucesso · HTTP 200", "sucesso · HTTP 200"],
    ]
    tbl = ax.table(cellText=matrix, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 2.7)
    fills = {
        (0, 0): "#111827",
        (0, 1): "#111827",
        (0, 2): "#111827",
        (1, 0): "#111827",
        (2, 0): "#111827",
        (1, 1): C1,
        (1, 2): C2,
        (2, 1): C3,
        (2, 2): C4,
    }
    for key, color in fills.items():
        cell = tbl[key]
        cell.set_facecolor(color)
        cell.set_text_props(color="white", weight="bold")
        cell.set_edgecolor("white")
    save(fig, "matriz-experimental-allowlist-versus-adulteracao.png")

    # 2. tabela parâmetros
    table_png(
        "Tabela: parâmetros essenciais do lote (n = 30)",
        ["Tratamento", "HTTP", "Tx", "Envio (ms)", "s envio", "Conf. (ms)", "s conf.", "Custo IOTA", "s custo"],
        [
            ["Com seg. + adulteração → falha", "403", "0/30", "—", "—", "—", "—", "0", "0 (sem tx)"],
            ["Com seg. + limpo → sucesso", "200", "30/30", br(series[1]["envio"]["mean"]), br(series[1]["envio"]["std"]), br(series[1]["conf"]["mean"]), br(series[1]["conf"]["std"]), br(series[1]["custo"]["mean"], 8), "0 (gas constante)"],
            ["Sem seg. + adulteração → sucesso", "200", "30/30", br(series[2]["envio"]["mean"]), br(series[2]["envio"]["std"]), br(series[2]["conf"]["mean"]), br(series[2]["conf"]["std"]), br(series[2]["custo"]["mean"], 8), "0 (gas constante)"],
            ["Sem seg. + limpo → sucesso", "200", "30/30", br(series[3]["envio"]["mean"]), br(series[3]["envio"]["std"]), br(series[3]["conf"]["mean"]), br(series[3]["conf"]["std"]), br(series[3]["custo"]["mean"], 8), "0 (gas constante)"],
        ],
        "tabela-parametros-essenciais-lote-30.png",
        figsize=(13.2, 3.5),
    )

    # 3. taxa de sucesso
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    taxa = [0, 100, 100, 100]
    bars = ax.bar(LABS, taxa, color=cores, width=0.55)
    ax.set_title("Taxa de sucesso no lote sequencial (não é teste de carga)", fontweight="bold")
    ax.set_ylabel("Taxa de sucesso (%)")
    ax.set_ylim(0, 120)
    for b, v in zip(bars, taxa):
        ax.text(b.get_x() + b.get_width() / 2, v + 3, f"{v:.0f}%", ha="center", weight="bold")
    save(fig, "taxa-de-sucesso-lote-sequencial-nao-e-carga.png")

    # 4. leituras aceitas
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    vals = [0, 30, 30, 30]
    bars = ax.bar(LABS, vals, color=cores, width=0.55)
    ax.set_title("Leituras aceitas (HTTP 200 + transação) no lote de 30", fontweight="bold")
    ax.set_ylabel("Leituras aceitas")
    ax.set_ylim(0, 38)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.6, str(v), ha="center", weight="bold")
    save(fig, "leituras-aceitas-http200-com-transacao.png")

    # 5. latência confirmação média
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    conf = [0, series[1]["conf"]["mean"], series[2]["conf"]["mean"], series[3]["conf"]["mean"]]
    sconf = [0, series[1]["conf"]["std"], series[2]["conf"]["std"], series[3]["conf"]["std"]]
    bars = ax.bar(LABS, conf, color=cores, width=0.55, yerr=sconf, capsize=6, ecolor="#111827")
    ax.set_title("Latência de confirmação on-chain (média ± desvio-padrão)", fontweight="bold")
    ax.set_ylabel("ms")
    ax.set_ylim(0, max(conf) * 1.35)
    ax.text(0, 220, "n/a\n(HTTP 403)", ha="center", color=C2, fontsize=9, weight="bold")
    for i, (b, m, sd) in enumerate(zip(bars, conf, sconf)):
        if m > 0:
            ax.text(b.get_x() + b.get_width() / 2, m + sd + 80, f"{m:.0f}\n±{sd:.0f}", ha="center", va="bottom", fontsize=9)
    save(fig, "latencia-de-confirmacao-on-chain-media-e-desvio-padrao.png")

    # 6. série confirmação
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    c1 = load("caso-01-com-seguranca-sem-adulteracao.csv")
    c3 = load("caso-03-sem-seguranca-sem-adulteracao.csv")
    c4 = load("caso-04-sem-seguranca-adulteracao.csv")
    for rows, lab, cor in (
        (c1, "Com segurança, limpo", C1),
        (c3, "Sem segurança, limpo", C3),
        (c4, "Sem segurança, adulterado", C4),
    ):
        ys = floats(rows, "tempo_confirmacao_ms")
        ax.plot(np.arange(1, len(ys) + 1), ys, color=cor, lw=1.7, marker="o", ms=3.5, label=lab)
    ax.set_title("Latência de confirmação on-chain por amostra", fontweight="bold")
    ax.set_xlabel("Amostra do lote")
    ax.set_ylabel("ms")
    ax.legend(frameon=False)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    save(fig, "latencia-de-confirmacao-on-chain-por-amostra.png")

    # 7. gás
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    gas = [0, 22109, 21725, 21725]
    bars = ax.bar(LABS, gas, color=cores, width=0.55)
    ax.set_title("Custo em gás por atestação (média do lote; s = 0)", fontweight="bold")
    ax.set_ylabel("Gas por transação")
    ax.text(0, 600, "n/a\n(sem tx)", ha="center", color=C2, fontsize=9, weight="bold")
    for i, (b, v) in enumerate(zip(bars, gas)):
        if v > 0:
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,}".replace(",", "."), ha="center", va="bottom")
    save(fig, "custo-em-gas-por-atestacao-media-s-zero.png")

    # 8. custo IOTA
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    means_u = [s["custo"]["mean"] * 1e6 for s in series]
    bars = ax.bar(xs, means_u, color=cores, width=0.62)
    ax.set_xticks(xs, LABS)
    ax.set_title("Custo em IOTA por transação (média; s = 0, gás constante)", fontweight="bold")
    ax.set_ylabel("µIOTA por transação")
    ax.set_ylim(0, max(means_u) * 1.42)
    for i, (b, s) in enumerate(zip(bars, series)):
        if not s["tem_tx"]:
            ax.text(b.get_x() + b.get_width() / 2, 12, "0 IOTA\n(sem tx)", ha="center", color=C2, fontsize=9, weight="bold")
        else:
            ax.text(
                b.get_x() + b.get_width() / 2,
                b.get_height() + 8,
                f"{br(s['custo']['mean'], 8)} IOTA\ns = 0",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    save(fig, "custo-em-iota-por-transacao-quatro-tratamentos.png")

    # 9. envio relay (não ESP32)
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    envio = [0, series[1]["envio"]["mean"], series[2]["envio"]["mean"], series[3]["envio"]["mean"]]
    senv = [0, series[1]["envio"]["std"], series[2]["envio"]["std"], series[3]["envio"]["std"]]
    bars = ax.bar(LABS, envio, color=cores, width=0.55, yerr=senv, capsize=6, ecolor="#111827")
    ax.set_title("Tempo de envio no relay — não é assinatura no ESP32", fontweight="bold")
    ax.set_ylabel("ms")
    ax.set_ylim(0, max(envio) * 1.45)
    ax.text(0, 80, "n/a\n(HTTP 403)", ha="center", color=C2, fontsize=9, weight="bold")
    for i, (b, m, sd) in enumerate(zip(bars, envio, senv)):
        if m > 0:
            ax.text(b.get_x() + b.get_width() / 2, m + sd + 40, f"{m:.0f}\n±{sd:.0f}", ha="center", va="bottom", fontsize=9)
    save(fig, "tempo-de-envio-no-relay-nao-e-assinatura-esp32.png")

    # 10. envio + confirmação
    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    envio_m = [0 if not s["tem_tx"] else s["envio"]["mean"] for s in series]
    envio_s = [0 if not s["tem_tx"] else s["envio"]["std"] for s in series]
    conf_m = [0 if not s["tem_tx"] else s["conf"]["mean"] for s in series]
    conf_s = [0 if not s["tem_tx"] else s["conf"]["std"] for s in series]
    w = 0.36
    ax.bar(xs - w / 2, envio_m, w, color="#93C5FD", yerr=envio_s, capsize=5, ecolor="#1F2937")
    ax.bar(xs + w / 2, conf_m, w, color=cores, yerr=conf_s, capsize=5, ecolor="#1F2937")
    ax.set_xticks(xs, LABS)
    ax.set_ylabel("ms")
    ax.set_title("Tempo de envio (relay) e confirmação on-chain (média ± s)", fontweight="bold")
    ax.legend(handles=[Patch(facecolor="#93C5FD", label="Envio no relay"), Patch(facecolor="#4B5563", label="Confirmação on-chain")], frameon=False, loc="upper left")
    ax.set_ylim(0, max(conf_m) * 1.4)
    ax.text(0, 400, "n/a\n(HTTP 403)", ha="center", color=C2, fontsize=9, weight="bold")
    save(fig, "tempo-envio-e-confirmacao-media-e-desvio-padrao.png")

    # 11–14 um PNG por tratamento
    titulos = [
        ("custo-e-tempo-com-seguranca-adulteracao-falha.png", "Custo e tempo: com segurança, adulteração, falha"),
        ("custo-e-tempo-com-seguranca-sem-adulteracao-sucesso.png", "Custo e tempo: com segurança, sem adulteração, sucesso"),
        ("custo-e-tempo-sem-seguranca-adulteracao-sucesso.png", "Custo e tempo: sem segurança, adulteração, sucesso"),
        ("custo-e-tempo-sem-seguranca-sem-adulteracao-sucesso.png", "Custo e tempo: sem segurança, sem adulteração, sucesso"),
    ]
    for s, (fname, titulo) in zip(series, titulos):
        fig = plt.figure(figsize=(10.6, 4.9))
        gs = fig.add_gridspec(2, 2, height_ratios=[0.16, 1], hspace=0.1, wspace=0.32)
        ax_title = fig.add_subplot(gs[0, :])
        ax_title.axis("off")
        ax_title.set_title(titulo, fontsize=13, fontweight="bold", color="#111827", pad=2)
        ax_c = fig.add_subplot(gs[1, 0])
        ax_t = fig.add_subplot(gs[1, 1])
        cor = s["cor"]
        custo_u = s["custo"]["mean"] * 1e6
        ax_c.bar(["Custo"], [custo_u], color=cor, width=0.45)
        ax_c.set_ylabel("µIOTA por transação")
        ax_c.set_title("Custo")
        ax_c.set_ylim(0, max(custo_u * 1.45, 80))
        if not s["tem_tx"]:
            ax_c.text(0, 8, "0 IOTA\ns = 0 (sem tx)", ha="center", va="bottom", fontsize=10, color=cor, fontweight="bold")
            ax_t.bar(["Envio", "Confirmação"], [0, 0], color=["#93C5FD", cor], width=0.55)
            ax_t.set_ylim(0, 100)
            ax_t.text(0.5, 45, "n/a\nsem transação", ha="center", fontsize=12, color=cor, fontweight="bold")
        else:
            ax_c.text(0, custo_u * 1.05, f"{br(s['custo']['mean'], 8)} IOTA\ns = 0", ha="center", va="bottom", fontsize=9)
            means = [s["envio"]["mean"], s["conf"]["mean"]]
            stds = [s["envio"]["std"], s["conf"]["std"]]
            ax_t.bar(["Envio", "Confirmação"], means, color=["#93C5FD", cor], width=0.55, yerr=stds, capsize=7, ecolor="#111827")
            ax_t.set_ylim(0, max(means[i] + stds[i] for i in range(2)) * 1.28)
            for i, (m, sd) in enumerate(zip(means, stds)):
                ax_t.text(i, m + sd + 80, f"{m:.0f} ms\n± {sd:.0f}", ha="center", va="bottom", fontsize=9)
        ax_t.set_ylabel("ms")
        ax_t.set_title("Tempo (média ± s)")
        save(fig, fname)

    print(f"\n{len(list(OUT.glob('*.png')))} PNGs em {OUT}")


if __name__ == "__main__":
    main()
