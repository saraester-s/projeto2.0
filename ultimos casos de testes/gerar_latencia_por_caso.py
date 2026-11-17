"""Um gráfico de latência de confirmação para cada tratamento."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from gerar_relatorio_pdf import C1, C2, C3, C4, floats, load, stats, style

OUT = Path(__file__).resolve().parent.parent / "figuras" / "png-com-titulo" / "latencia-confirmacao"
DPI = 300

CASOS = [
    {
        "csv": "caso-02-com-seguranca-adulteracao.csv",
        "cor": C2,
        "tem_tx": False,
        "arquivo": "latencia-confirmacao-com-seguranca-adulteracao-falha.png",
        "titulo": "Latência de confirmação: com segurança, adulteração, falha",
    },
    {
        "csv": "caso-01-com-seguranca-sem-adulteracao.csv",
        "cor": C1,
        "tem_tx": True,
        "arquivo": "latencia-confirmacao-com-seguranca-sem-adulteracao-sucesso.png",
        "titulo": "Latência de confirmação: com segurança, sem adulteração, sucesso",
    },
    {
        "csv": "caso-04-sem-seguranca-adulteracao.csv",
        "cor": C4,
        "tem_tx": True,
        "arquivo": "latencia-confirmacao-sem-seguranca-adulteracao-sucesso.png",
        "titulo": "Latência de confirmação: sem segurança, adulteração, sucesso",
    },
    {
        "csv": "caso-03-sem-seguranca-sem-adulteracao.csv",
        "cor": C3,
        "tem_tx": True,
        "arquivo": "latencia-confirmacao-sem-seguranca-sem-adulteracao-sucesso.png",
        "titulo": "Latência de confirmação: sem segurança, sem adulteração, sucesso",
    },
]


def main() -> None:
    style()
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 13, "axes.labelsize": 10})
    OUT.mkdir(parents=True, exist_ok=True)

    for caso in CASOS:
        rows = load(caso["csv"])
        ys = floats(rows, "tempo_confirmacao_ms")
        fig, ax = plt.subplots(figsize=(8.4, 4.4))
        ax.set_title(caso["titulo"], fontweight="bold")
        if not caso["tem_tx"] or not ys:
            ax.set_ylim(0, 100)
            ax.set_ylabel("ms")
            ax.set_xlabel("Amostra do lote")
            ax.set_xticks([])
            ax.text(0.5, 0.5, "n/a\nHTTP 403 — sem transação\nsem latência on-chain", ha="center", va="center", transform=ax.transAxes, color=caso["cor"], fontsize=14, fontweight="bold")
        else:
            st = stats(ys)
            xs = np.arange(1, len(ys) + 1)
            ax.plot(xs, ys, color=caso["cor"], lw=1.8, marker="o", ms=4.5)
            ax.axhline(st["mean"], color="#6B7280", ls="--", lw=1.1, label=f"média {st['mean']:.0f} ms")
            ax.fill_between(xs, st["mean"] - st["std"], st["mean"] + st["std"], color=caso["cor"], alpha=0.12, label=f"± s ({st['std']:.0f} ms)")
            ax.set_ylabel("Tempo de confirmação (ms)")
            ax.set_xlabel("Amostra do lote")
            ax.legend(frameon=False, loc="upper right")
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.annotate(
                f"n = {int(st['n'])}   média = {st['mean']:.0f} ms   s = {st['std']:.0f} ms",
                xy=(0.0, -0.18),
                xycoords="axes fraction",
                fontsize=9,
                color="#374151",
            )
        path = OUT / caso["arquivo"]
        fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.25, facecolor="white")
        plt.close(fig)
        print(path.name)


if __name__ == "__main__":
    main()
