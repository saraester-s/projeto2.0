"""Quatro resultados na ordem pedida: custo e tempo, valores no gráfico, ±s."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from gerar_relatorio_pdf import C1, C2, C3, C4, br, floats, load, stats, style

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figuras-artigo"
DPI = 300

ORDEM = [
    {
        "csv": "caso-02-com-seguranca-adulteracao.csv",
        "titulo": "Com segurança\nadulteração\nfalha",
        "cor": C2,
        "tem_tx": False,
    },
    {
        "csv": "caso-01-com-seguranca-sem-adulteracao.csv",
        "titulo": "Com segurança\nsem adulteração\nsucesso",
        "cor": C1,
        "tem_tx": True,
    },
    {
        "csv": "caso-04-sem-seguranca-adulteracao.csv",
        "titulo": "Sem segurança\nadulteração\nsucesso",
        "cor": C4,
        "tem_tx": True,
    },
    {
        "csv": "caso-03-sem-seguranca-sem-adulteracao.csv",
        "titulo": "Sem segurança\nsem adulteração\nsucesso",
        "cor": C3,
        "tem_tx": True,
    },
]


def save(fig, name: str) -> None:
    path = OUT / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.2, facecolor="white")
    plt.close(fig)
    print(path.name)


def pack(item: dict) -> dict:
    rows = load(item["csv"])
    custo = floats(rows, "custo_iota")
    envio = floats(rows, "tempo_envio_ms")
    conf = floats(rows, "tempo_confirmacao_ms")
    if not item["tem_tx"]:
        custo = [0.0] * len(rows)
    return {
        **item,
        "n": len(rows),
        "custo": stats(custo),
        "envio": stats(envio),
        "conf": stats(conf),
    }


def rotulos(series: list[dict]) -> list[str]:
    return [s["titulo"] for s in series]


def main() -> None:
    style()
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 13, "axes.labelsize": 10})
    OUT.mkdir(parents=True, exist_ok=True)
    series = [pack(item) for item in ORDEM]
    xs = np.arange(len(series))
    cores = [s["cor"] for s in series]
    labs = rotulos(series)

    # --- CUSTO (µIOTA para o eixo ser legível) ---
    means_u = [s["custo"]["mean"] * 1e6 for s in series]
    stds_u = [s["custo"]["std"] * 1e6 for s in series]
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    bars = ax.bar(xs, means_u, color=cores, width=0.62, yerr=stds_u, capsize=6, ecolor="#111827", error_kw={"lw": 1.2})
    ax.set_xticks(xs, labs)
    ax.set_ylabel("Custo médio (µIOTA por transação)")
    ax.set_title("Custo — quatro resultados (média ± desvio-padrão)")
    ymax = max(means_u) * 1.42 if max(means_u) else 1
    ax.set_ylim(0, ymax)
    for i, (b, s) in enumerate(zip(bars, series)):
        m, sd = s["custo"]["mean"], s["custo"]["std"]
        if not s["tem_tx"]:
            txt = "0\ns = 0\n(sem tx)"
        elif sd < 1e-12:
            txt = f"{br(m, 8)} IOTA\n{br(m * 1e6, 2)} µIOTA\ns = 0 (gas constante)"
        else:
            txt = f"{br(m, 8)} IOTA\n± {br(sd, 8)}"
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + ymax * 0.03, txt, ha="center", va="bottom", fontsize=8)
    ax.annotate(
        "Aviso: nos casos com transação o gas (e o custo) foi idêntico em todas as amostras, então s = 0.",
        xy=(0, -0.28),
        xycoords="axes fraction",
        fontsize=8.5,
        color="#374151",
    )
    save(fig, "ordem-01-custo.png")

    # --- TEMPO (envio + confirmação) ---
    envio_m = [s["envio"]["mean"] if s["tem_tx"] else 0 for s in series]
    envio_s = [s["envio"]["std"] if s["tem_tx"] else 0 for s in series]
    conf_m = [s["conf"]["mean"] if s["tem_tx"] else 0 for s in series]
    conf_s = [s["conf"]["std"] if s["tem_tx"] else 0 for s in series]
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    w = 0.36
    from matplotlib.patches import Patch

    b1 = ax.bar(xs - w / 2, envio_m, w, color="#93C5FD", yerr=envio_s, capsize=5, ecolor="#1F2937", error_kw={"lw": 1.1})
    b2 = ax.bar(xs + w / 2, conf_m, w, color=cores, yerr=conf_s, capsize=5, ecolor="#1F2937", error_kw={"lw": 1.1})
    ax.set_xticks(xs, labs)
    ax.set_ylabel("Tempo (ms)")
    ax.set_title("Tempo — quatro resultados (média ± desvio-padrão)")
    ax.legend(
        handles=[Patch(facecolor="#93C5FD", label="Envio (relay)"), Patch(facecolor="#4B5563", label="Confirmação on-chain")],
        frameon=False,
        loc="upper left",
    )
    ax.set_ylim(0, max(conf_m) * 1.42)
    ax.text(0, 420, "n/a\n(HTTP 403, sem tx)", ha="center", color=C2, fontsize=9, weight="bold")
    for bars, means, stds in ((b1, envio_m, envio_s), (b2, conf_m, conf_s)):
        for i, (b, m, sd) in enumerate(zip(bars, means, stds)):
            if m <= 0:
                continue
            ax.text(
                b.get_x() + b.get_width() / 2,
                m + sd + 80,
                f"{m:.0f}\n±{sd:.0f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    ax.annotate(
        "Aviso: há desvio-padrão no tempo (envio e confirmação). No 1º resultado não há tempo: o relay recusou antes da tx.",
        xy=(0, -0.28),
        xycoords="axes fraction",
        fontsize=8.5,
        color="#374151",
    )
    save(fig, "ordem-02-tempo.png")

    # --- tabela resumo na mesma ordem ---
    fig, ax = plt.subplots(figsize=(12.2, 3.6))
    ax.axis("off")
    ax.set_title("Custo e tempo na ordem dos quatro resultados (n = 30)", loc="left", fontsize=12, pad=8)
    headers = [
        "Resultado",
        "Custo médio (IOTA)",
        "s custo",
        "Envio médio (ms)",
        "s envio",
        "Conf. média (ms)",
        "s conf.",
    ]
    body = []
    nomes = [
        "1. Com seg. + adulteração → falha",
        "2. Com seg. + sem adulteração → sucesso",
        "3. Sem seg. + adulteração → sucesso",
        "4. Sem seg. + sem adulteração → sucesso",
    ]
    for nome, s in zip(nomes, series):
        if s["tem_tx"]:
            body.append(
                [
                    nome,
                    br(s["custo"]["mean"], 8),
                    "0 (gas constante)",
                    br(s["envio"]["mean"]),
                    br(s["envio"]["std"]),
                    br(s["conf"]["mean"]),
                    br(s["conf"]["std"]),
                ]
            )
        else:
            body.append([nome, "0", "0 (sem tx)", "—", "—", "—", "—"])
    table = ax.table(cellText=body, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2.05)
    widths = [0.30, 0.13, 0.13, 0.12, 0.10, 0.12, 0.10]
    for i, w in enumerate(widths):
        for r in range(len(body) + 1):
            table[(r, i)].set_width(w)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#E5E7EB")
        if r == 0:
            cell.set_facecolor("#111827")
            cell.set_text_props(color="white", weight="bold")
        else:
            cell.set_facecolor(series[r - 1]["cor"] if c == 0 else ("#F9FAFB" if r % 2 == 0 else "white"))
            if c == 0:
                cell.set_text_props(color="white", weight="bold", fontsize=7)
    save(fig, "ordem-03-tabela-custo-tempo.png")

    print("ok")


ARQUIVOS_CASO = [
    "caso-01-com-seguranca-adulteracao-falha.png",
    "caso-02-com-seguranca-sem-adulteracao-sucesso.png",
    "caso-03-sem-seguranca-adulteracao-sucesso.png",
    "caso-04-sem-seguranca-sem-adulteracao-sucesso.png",
]

TITULOS_CASO = [
    "Caso 1",
    "Caso 2",
    "Caso 3",
    "Caso 4",
]


def figura_um_caso(s: dict, titulo: str, arquivo: str) -> None:
    fig = plt.figure(figsize=(10.6, 4.9))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.14, 1], hspace=0.08, wspace=0.32)
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis("off")
    ax_title.set_title(titulo, fontsize=14, fontweight="bold", color="#111827", pad=2)
    ax_c = fig.add_subplot(gs[1, 0])
    ax_t = fig.add_subplot(gs[1, 1])
    cor = s["cor"]

    custo_u = s["custo"]["mean"] * 1e6
    ax_c.bar(["Custo"], [custo_u], color=cor, width=0.45)
    ax_c.set_ylabel("µIOTA por transação")
    ax_c.set_title("Custo")
    ax_c.set_ylim(0, max(custo_u * 1.45, 80))
    if not s["tem_tx"]:
        ax_c.text(0, 8, "0 IOTA\ns = 0\n(sem tx · HTTP 403)", ha="center", va="bottom", fontsize=10, color=cor, fontweight="bold")
    else:
        ax_c.text(
            0,
            custo_u + ax_c.get_ylim()[1] * 0.04,
            f"{br(s['custo']['mean'], 8)} IOTA\n{br(custo_u, 2)} µIOTA\ns = 0 (gas constante)",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    cats = ["Envio", "Confirmação"]
    if s["tem_tx"]:
        means = [s["envio"]["mean"], s["conf"]["mean"]]
        stds = [s["envio"]["std"], s["conf"]["std"]]
        ax_t.bar(cats, means, color=["#93C5FD", cor], width=0.55, yerr=stds, capsize=7, ecolor="#111827")
        ax_t.set_ylim(0, max(means[i] + stds[i] for i in range(2)) * 1.28)
        for i, (m, sd) in enumerate(zip(means, stds)):
            ax_t.text(i, m + sd + 80, f"{m:.0f} ms\n± {sd:.0f}", ha="center", va="bottom", fontsize=9)
        aviso = "Há desvio-padrão no tempo (n = 30)."
    else:
        ax_t.bar(cats, [0, 0], color=["#93C5FD", cor], width=0.55)
        ax_t.set_ylim(0, 100)
        ax_t.text(0.5, 45, "n/a\nsem transação\nHTTP 403", ha="center", va="center", fontsize=12, color=cor, fontweight="bold")
        aviso = "Sem desvio-padrão de tempo: o relay recusou antes da tx."
    ax_t.set_ylabel("ms")
    ax_t.set_title("Tempo (média ± s)")
    fig.text(0.5, -0.04, aviso, ha="center", fontsize=9, color="#374151")
    save(fig, arquivo)


def figuras_individuais() -> None:
    style()
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10})
    OUT.mkdir(parents=True, exist_ok=True)
    series = [pack(item) for item in ORDEM]
    for s, titulo, arquivo in zip(series, TITULOS_CASO, ARQUIVOS_CASO):
        figura_um_caso(s, titulo, arquivo)


if __name__ == "__main__":
    figuras_individuais()
