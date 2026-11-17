"""PNGs por caso: tempo de assinatura no ESP32 (não medido no experimento)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from gerar_relatorio_pdf import C1, C2, C3, C4, style

OUT = Path(__file__).resolve().parent.parent / "figuras" / "png-com-titulo" / "tempo-assinatura-esp32"
DPI = 300

CASOS = [
    {
        "cor": C2,
        "arquivo": "tempo-assinatura-esp32-com-seguranca-adulteracao-falha.png",
        "titulo": "Tempo de assinatura no ESP32: com segurança, adulteração, falha",
    },
    {
        "cor": C1,
        "arquivo": "tempo-assinatura-esp32-com-seguranca-sem-adulteracao-sucesso.png",
        "titulo": "Tempo de assinatura no ESP32: com segurança, sem adulteração, sucesso",
    },
    {
        "cor": C4,
        "arquivo": "tempo-assinatura-esp32-sem-seguranca-adulteracao-sucesso.png",
        "titulo": "Tempo de assinatura no ESP32: sem segurança, adulteração, sucesso",
    },
    {
        "cor": C3,
        "arquivo": "tempo-assinatura-esp32-sem-seguranca-sem-adulteracao-sucesso.png",
        "titulo": "Tempo de assinatura no ESP32: sem segurança, sem adulteração, sucesso",
    },
]


def main() -> None:
    style()
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 13})
    OUT.mkdir(parents=True, exist_ok=True)

    for caso in CASOS:
        fig, ax = plt.subplots(figsize=(8.4, 4.4))
        ax.set_title(caso["titulo"], fontweight="bold")
        ax.set_ylabel("ms")
        ax.set_xlabel("Amostra do lote")
        ax.set_ylim(0, 100)
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        ax.text(
            0.5,
            0.58,
            "não medido",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color=caso["cor"],
            fontsize=16,
            fontweight="bold",
        )
        ax.text(
            0.5,
            0.36,
            "O ESP32 só envia POST HTTP.\nA assinatura EVM é feita no PC do relay.\nNão há coluna de tempo de assinatura no CSV.",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color="#374151",
            fontsize=10,
        )
        path = OUT / caso["arquivo"]
        fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.25, facecolor="white")
        plt.close(fig)
        print(path.name)


if __name__ == "__main__":
    main()
