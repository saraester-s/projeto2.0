"""Taxa de sucesso por caso (lote sequencial; não é teste de carga)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator, PercentFormatter

from gerar_relatorio_pdf import C1, C2, C3, C4, load, style

OUT = Path(__file__).resolve().parent.parent / "figuras" / "png-com-titulo" / "taxa-sucesso-lote-sequencial"
DPI = 300

CASOS = [
    {
        "csv": "caso-02-com-seguranca-adulteracao.csv",
        "cor": C2,
        "arquivo": "taxa-sucesso-lote-sequencial-com-seguranca-adulteracao-falha.png",
        "titulo": "Taxa de sucesso (lote sequencial, não carga): com segurança, adulteração, falha",
    },
    {
        "csv": "caso-01-com-seguranca-sem-adulteracao.csv",
        "cor": C1,
        "arquivo": "taxa-sucesso-lote-sequencial-com-seguranca-sem-adulteracao-sucesso.png",
        "titulo": "Taxa de sucesso (lote sequencial, não carga): com segurança, sem adulteração, sucesso",
    },
    {
        "csv": "caso-04-sem-seguranca-adulteracao.csv",
        "cor": C4,
        "arquivo": "taxa-sucesso-lote-sequencial-sem-seguranca-adulteracao-sucesso.png",
        "titulo": "Taxa de sucesso (lote sequencial, não carga): sem segurança, adulteração, sucesso",
    },
    {
        "csv": "caso-03-sem-seguranca-sem-adulteracao.csv",
        "cor": C3,
        "arquivo": "taxa-sucesso-lote-sequencial-sem-seguranca-sem-adulteracao-sucesso.png",
        "titulo": "Taxa de sucesso (lote sequencial, não carga): sem segurança, sem adulteração, sucesso",
    },
]


def main() -> None:
    style()
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12})
    OUT.mkdir(parents=True, exist_ok=True)

    for caso in CASOS:
        rows = load(caso["csv"])
        ok = np.array([1.0 if (r.get("status") or "") == "success" else 0.0 for r in rows])
        n = len(ok)
        taxa = 100.0 * float(ok.mean()) if n else 0.0
        n_ok = int(ok.sum())
        xs = np.arange(1, n + 1)
        cumul = 100.0 * np.cumsum(ok) / xs

        fig, (ax_bar, ax_seq) = plt.subplots(1, 2, figsize=(10.8, 4.5), gridspec_kw={"width_ratios": [0.7, 1.3]})
        fig.suptitle(caso["titulo"], fontsize=12, fontweight="bold", y=1.02)

        ax_bar.bar(["Lote"], [taxa], color=caso["cor"], width=0.45)
        ax_bar.set_ylim(0, 118)
        ax_bar.set_ylabel("Taxa de sucesso (%)")
        ax_bar.set_title("Taxa do lote")
        ax_bar.text(0, taxa + 4, f"{taxa:.0f}%\n{n_ok}/{n}", ha="center", va="bottom", fontsize=11, fontweight="bold", color=caso["cor"])

        ax_seq.step(xs, 100 * ok, where="mid", color=caso["cor"], lw=1.8, label="sucesso da amostra (0/100%)")
        ax_seq.plot(xs, cumul, color="#6B7280", ls="--", lw=1.2, label="taxa acumulada")
        ax_seq.set_ylim(-8, 118)
        ax_seq.set_xlabel("Amostra (intervalo ~10 s, sequencial)")
        ax_seq.set_ylabel("%")
        ax_seq.set_title("Por amostra")
        ax_seq.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax_seq.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax_seq.legend(frameon=False, loc="best", fontsize=8)

        fig.text(
            0.5,
            -0.06,
            "Não é teste de carga: 30 POSTs em série, ~10 s entre envios. A taxa mede aceite/rejeição do protocolo, não throughput.",
            ha="center",
            fontsize=8.5,
            color="#374151",
        )
        path = OUT / caso["arquivo"]
        fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.28, facecolor="white")
        plt.close(fig)
        print(path.name, f"{n_ok}/{n} = {taxa:.0f}%")


if __name__ == "__main__":
    main()
