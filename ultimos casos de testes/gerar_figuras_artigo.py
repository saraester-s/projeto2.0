"""Exporta cada gráfico e tabela do relatório como PNG 300 dpi para o artigo."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from gerar_relatorio_pdf import (
    C1,
    C2,
    C3,
    C4,
    br,
    floats,
    load,
    stats,
    style,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figuras-artigo"
DPI = 300
LABELS = ["Caso 1", "Caso 2", "Caso 3", "Caso 4"]
CORES = [C1, C2, C3, C4]


def save(fig, name: str) -> Path:
    path = OUT / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.18, facecolor="white")
    plt.close(fig)
    print(path.name)
    return path


def table_fig(headers, rows, *, header_color="#111827", figsize, fontsize=9, col_widths=None, title=None):
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=12, pad=10, loc="left", color="#111827")
    table = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, 1.55)
    if col_widths:
        for i, w in enumerate(col_widths):
            for r in range(len(rows) + 1):
                table[(r, i)].set_width(w)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#E5E7EB")
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", weight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#F9FAFB")
    return fig


def metric_rows(st_envio, st_conf, st_gas):
    if not st_envio["n"]:
        return [
            ["Envio (ms)", "—", "—", "—", "sem transação"],
            ["Confirmação (ms)", "—", "—", "—", "sem transação"],
            ["Gas por tx", "—", "—", "—", "sem transação"],
        ]
    return [
        [
            "Envio (ms)",
            br(st_envio["mean"]),
            br(st_envio["std"]),
            f"[{br(st_envio['ci_lo'])} ; {br(st_envio['ci_hi'])}]",
            f"{br(st_envio['mn'])}–{br(st_envio['mx'])}",
        ],
        [
            "Confirmação (ms)",
            br(st_conf["mean"]),
            br(st_conf["std"]),
            f"[{br(st_conf['ci_lo'])} ; {br(st_conf['ci_hi'])}]",
            f"{br(st_conf['mn'])}–{br(st_conf['mx'])}",
        ],
        [
            "Gas por tx",
            br(st_gas["mean"], 0),
            br(st_gas["std"], 0),
            f"[{br(st_gas['ci_lo'], 0)} ; {br(st_gas['ci_hi'], 0)}]",
            br(st_gas["mean"], 0),
        ],
    ]


def series_plot(vals, *, title, ylabel, color, name):
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    xs = np.arange(1, len(vals) + 1)
    ax.plot(xs, vals, color=color, lw=1.8, marker="o", ms=4)
    ax.axhline(float(np.mean(vals)), color="#6B7280", ls="--", lw=1, label="média")
    ax.set_title(title)
    ax.set_xlabel("Amostra do lote")
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    save(fig, name)


def amostras_body(rows, com_tx: bool):
    body = []
    for i, r in enumerate(rows, 1):
        if com_tx:
            tx = (r.get("tx_hash") or "")[:18] + "…" if r.get("tx_hash") else "—"
            body.append(
                [
                    str(i),
                    (r.get("quando") or "")[5:],
                    r.get("status") or "",
                    br(float(r["tempo_envio_ms"])) if r.get("tempo_envio_ms") else "—",
                    br(float(r["tempo_confirmacao_ms"])) if r.get("tempo_confirmacao_ms") else "—",
                    r.get("gas_usado") or "—",
                    r.get("custo_iota") or "—",
                    r.get("temperature") or "—",
                    r.get("humidity") or "—",
                    tx,
                ]
            )
        else:
            msg = r.get("mensagem") or ""
            if len(msg) > 72:
                msg = msg[:69] + "…"
            body.append(
                [
                    str(i),
                    (r.get("quando") or "")[5:],
                    r.get("status") or "",
                    r.get("temperature") or "—",
                    r.get("humidity") or "—",
                    msg,
                ]
            )
    return body


def main() -> None:
    style()
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10})
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()

    c1 = load("caso-01-com-seguranca-sem-adulteracao.csv")
    c2 = load("caso-02-com-seguranca-adulteracao.csv")
    c3 = load("caso-03-sem-seguranca-sem-adulteracao.csv")
    c4 = load("caso-04-sem-seguranca-adulteracao.csv")

    def pack(rows):
        e, c, g = floats(rows, "tempo_envio_ms"), floats(rows, "tempo_confirmacao_ms"), floats(rows, "gas_usado")
        return {"rows": rows, "envio_s": e, "conf_s": c, "gas_s": g, "envio": stats(e), "conf": stats(c), "gas": stats(g)}

    cases = {"1": pack(c1), "2": pack(c2), "3": pack(c3), "4": pack(c4)}

    # --- matriz 2x2 ---
    fig, ax = plt.subplots(figsize=(8.4, 2.8))
    ax.axis("off")
    ax.set_title("Desenho experimental dos quatro casos", loc="left", fontsize=12, pad=8)
    matrix = [
        ["", "Firmware limpo", "Firmware adulterado"],
        ["Com segurança\nPOST /atestar :5000", "Caso 1 — sucesso\n30/30 · HTTP 200", "Caso 2 — falha\n0/30 · HTTP 403"],
        ["Sem segurança\nPOST /leitura :5001", "Caso 3 — sucesso\n30/30 · HTTP 200", "Caso 4 — sucesso*\n30/30 · HTTP 200"],
    ]
    tbl = ax.table(cellText=matrix, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 2.8)
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
    save(fig, "tab-00-matriz-experimental.png")

    # --- tabela comparação ---
    fig = table_fig(
        ["Caso", "Segurança", "Adulteração", "HTTP", "Tx", "Envio (ms)", "Conf. (ms)", "Gas", "IOTA/tx", "IOTA lote"],
        [
            ["1", "com", "não", "200", "30/30", "1 638,23", "4 673,75", "22 109", "0,000221", "0,0066327"],
            ["2", "com", "sim", "403", "0/30", "—", "—", "—", "0", "0"],
            ["3", "sem", "não", "200", "30/30", "1 664,76", "4 384,17", "21 725", "0,000217", "0,0065175"],
            ["4", "sem", "sim", "200", "30/30", "1 481,69", "4 154,59", "21 725", "0,000217", "0,0065175"],
        ],
        figsize=(11.2, 2.4),
        fontsize=8.5,
        title="Parâmetros essenciais do lote de 30 amostras",
    )
    save(fig, "tab-01-comparacao-lote.png")

    # --- leituras aceitas ---
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    vals = [30, 0, 30, 30]
    bars = ax.bar(LABELS, vals, color=CORES, width=0.55)
    ax.set_ylabel("Leituras aceitas (HTTP 200 + transação)")
    ax.set_title("Leituras aceitas no lote de 30")
    ax.set_ylim(0, 38)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.6, str(v), ha="center", weight="bold")
    save(fig, "fig-01-leituras-aceitas.png")

    # --- envio + confirmação ---
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    envio = [
        cases["1"]["envio"]["mean"],
        0,
        cases["3"]["envio"]["mean"],
        cases["4"]["envio"]["mean"],
    ]
    conf = [
        cases["1"]["conf"]["mean"],
        0,
        cases["3"]["conf"]["mean"],
        cases["4"]["conf"]["mean"],
    ]
    x = np.arange(4)
    w = 0.36
    b1 = ax.bar(x - w / 2, envio, w, color="#93C5FD", label="Envio")
    b2 = ax.bar(x + w / 2, conf, w, color=CORES, label="Confirmação")
    ax.set_xticks(x, LABELS)
    ax.set_ylabel("Tempo (ms)")
    ax.set_title("Tempo médio de envio e de confirmação on-chain")
    ax.legend(frameon=False)
    ax.text(1, 140, "n/a", ha="center", color=C2, fontsize=10)
    for b in list(b1) + list(b2):
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width() / 2, h, f"{h:.0f}", ha="center", va="bottom", fontsize=8)
    save(fig, "fig-02-latencia-envio-confirmacao.png")

    # --- barras separadas (como no PDF antigo / artigo) ---
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    envio_plot = [cases["1"]["envio"]["mean"], 0, cases["3"]["envio"]["mean"], cases["4"]["envio"]["mean"]]
    bars = ax.bar(LABELS, envio_plot, color=CORES, width=0.55)
    ax.set_ylabel("Milissegundos")
    ax.set_title("Tempo médio de envio da transação")
    for i, (b, v) in enumerate(zip(bars, envio_plot)):
        if i == 1:
            ax.text(b.get_x() + b.get_width() / 2, 40, "n/a", ha="center", color=C2)
        else:
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}", ha="center", va="bottom")
    save(fig, "fig-03-tempo-envio.png")

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    conf_plot = [cases["1"]["conf"]["mean"], 0, cases["3"]["conf"]["mean"], cases["4"]["conf"]["mean"]]
    bars = ax.bar(LABELS, conf_plot, color=CORES, width=0.55)
    ax.set_ylabel("Milissegundos")
    ax.set_title("Tempo médio até confirmação on-chain")
    for i, (b, v) in enumerate(zip(bars, conf_plot)):
        if i == 1:
            ax.text(b.get_x() + b.get_width() / 2, 80, "n/a", ha="center", color=C2)
        else:
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}", ha="center", va="bottom")
    save(fig, "fig-04-tempo-confirmacao.png")

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    custo = [0.0066327, 0.0, 0.0065175, 0.0065175]
    bars = ax.bar(LABELS, custo, color=CORES, width=0.55)
    ax.set_ylabel("IOTA (lote de 30)")
    ax.set_title("Custo total do lote de 30")
    for b, v in zip(bars, custo):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{br(v, 7)}", ha="center", va="bottom", fontsize=8)
    save(fig, "fig-05-custo-total.png")

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    gas = [cases["1"]["gas"]["mean"], 0, cases["3"]["gas"]["mean"], cases["4"]["gas"]["mean"]]
    bars = ax.bar(LABELS, gas, color=CORES, width=0.55)
    ax.set_ylabel("Gas por transação")
    ax.set_title("Custo em gás por atestação (média do lote)")
    for i, (b, v) in enumerate(zip(bars, gas)):
        if i == 1:
            ax.text(b.get_x() + b.get_width() / 2, 400, "n/a", ha="center", color=C2)
        else:
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}".replace(",", "."), ha="center", va="bottom")
    save(fig, "fig-06-gas-por-tx.png")

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    taxa = [100, 0, 100, 100]
    bars = ax.bar(LABELS, taxa, color=CORES, width=0.55)
    ax.set_ylabel("Taxa de sucesso (%)")
    ax.set_ylim(0, 118)
    ax.set_title("Taxa de sucesso no lote (sequencial, ~10 s)")
    for b, v in zip(bars, taxa):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.0f}%", ha="center", weight="bold")
    save(fig, "fig-07-taxa-sucesso.png")

    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    for key, color, lab in (("1", C1, "Caso 1"), ("3", C3, "Caso 3"), ("4", C4, "Caso 4")):
        xs = np.arange(1, len(cases[key]["envio_s"]) + 1)
        ax.plot(xs, cases[key]["envio_s"], color=color, lw=1.7, marker="o", ms=3.5, label=lab)
    ax.set_title("Tempo de envio por amostra")
    ax.set_xlabel("Amostra do lote")
    ax.set_ylabel("ms")
    ax.legend(frameon=False, ncol=3)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    save(fig, "fig-08-serie-envio.png")

    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    for key, color, lab in (("1", C1, "Caso 1"), ("3", C3, "Caso 3"), ("4", C4, "Caso 4")):
        xs = np.arange(1, len(cases[key]["conf_s"]) + 1)
        ax.plot(xs, cases[key]["conf_s"], color=color, lw=1.7, marker="o", ms=3.5, label=lab)
    ax.set_title("Tempo de confirmação on-chain por amostra")
    ax.set_xlabel("Amostra do lote")
    ax.set_ylabel("ms")
    ax.legend(frameon=False, ncol=3)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    save(fig, "fig-09-serie-confirmacao.png")

    fichas = {
        "1": (
            C1,
            "Caso 1 — com segurança, sem adulteração",
            [
                ("Segurança", "com — POST /atestar :5000"),
                ("Adulteração", "não"),
                ("Resultado", "sucesso · HTTP 200 + tx_hash · 30/30"),
                ("Quando", "2026-10-27 17:05:53 → 2026-10-29 15:56:14"),
                ("Hash enrolado", "8422ebe782c2f51ab17c330621d0b4c2c29db4175a82929fec0bab04d2ba28b6"),
                ("Custo médio / total", "0,000221 IOTA · 0,0066327 IOTA no lote"),
            ],
            c1,
            True,
        ),
        "2": (
            C2,
            "Caso 2 — com segurança, adulteração",
            [
                ("Segurança", "com — POST /atestar :5000"),
                ("Adulteração", "sim — Serial.println no .ino"),
                ("Resultado", "falha · HTTP 403 · 0 transações"),
                ("Quando", "2026-10-29 16:12:29 → 16:17:24"),
                ("Hash enrolado", "8422ebe7…d2ba28b6"),
                ("Hash apresentado", "665704c91f218e2e3f8b13c595ec15898215f4b9ed65af0664448c7e1a84a275"),
                ("Mensagem", "Hash de firmware nao enrolado. Codigo alterado nao e aceito."),
                ("DHT11", "24,9–25,0 °C · umidade 67–68 %"),
            ],
            c2,
            False,
        ),
        "3": (
            C3,
            "Caso 3 — sem segurança, sem adulteração",
            [
                ("Segurança", "sem — POST /leitura :5001"),
                ("Adulteração", "não"),
                ("Resultado", "sucesso · HTTP 200 + tx_hash · 30/30"),
                ("Quando", "2026-10-29 16:42:11 → 16:49:23"),
                ("Hash on-chain", "zeros (HASH_SEM_ATESTACAO); relay sem allowlist"),
                ("DHT11", "25,2–25,3 °C · umidade 66 %"),
                ("Custo médio / total", "0,000217 IOTA · 0,0065175 IOTA no lote"),
            ],
            c3,
            True,
        ),
        "4": (
            C4,
            "Caso 4 — sem segurança, adulteração",
            [
                ("Segurança", "sem — POST /leitura :5001"),
                ("Adulteração", "sim — o mesmo Serial.println do caso 2"),
                ("Resultado", "sucesso HTTP 200 — chain não detecta a adulteração"),
                ("Quando", "2026-10-29 17:02:38 → 17:09:33"),
                ("Hash on-chain", "zeros; ninguém confere firmware"),
                ("DHT11", "25,1–25,2 °C · umidade 66 %"),
                ("Custo médio / total", "0,000217 IOTA · 0,0065175 IOTA no lote (idêntico ao caso 3)"),
            ],
            c4,
            True,
        ),
    }

    for num, (cor, titulo, ficha, rows, com_tx) in fichas.items():
        fig = table_fig(
            ["Campo", "Valor"],
            [[a, b] for a, b in ficha],
            header_color=cor,
            figsize=(9.2, 0.55 * (len(ficha) + 3)),
            fontsize=9,
            col_widths=[0.28, 0.72],
            title=titulo,
        )
        save(fig, f"tab-caso-0{num}-ficha.png")

        fig = table_fig(
            ["Métrica", "Média", "s", "IC 95% (t, gl=29)", "min–máx"],
            metric_rows(cases[num]["envio"], cases[num]["conf"], cases[num]["gas"]),
            header_color=cor,
            figsize=(9.4, 2.2),
            fontsize=9,
            title=f"Caso {num} — médias do lote 30",
        )
        save(fig, f"tab-caso-0{num}-metricas.png")

        if com_tx:
            series_plot(
                cases[num]["envio_s"],
                title=f"Caso {num} — tempo de envio da transação (relay)",
                ylabel="ms",
                color=cor,
                name=f"fig-caso-0{num}-envio.png",
            )
            series_plot(
                cases[num]["conf_s"],
                title=f"Caso {num} — latência de confirmação on-chain",
                ylabel="ms",
                color=cor,
                name=f"fig-caso-0{num}-confirmacao.png",
            )
            series_plot(
                cases[num]["gas_s"],
                title=f"Caso {num} — gas usado por transação",
                ylabel="gas",
                color=cor,
                name=f"fig-caso-0{num}-gas.png",
            )
            headers = ["#", "quando", "status", "envio ms", "conf. ms", "gas", "IOTA", "T °C", "U %", "tx"]
            widths = [0.04, 0.13, 0.08, 0.09, 0.09, 0.07, 0.10, 0.07, 0.07, 0.16]
        else:
            fig, ax = plt.subplots(figsize=(5.2, 3.8))
            ax.bar(["Firmware adulterado"], [0], color=cor, width=0.45)
            ax.set_ylim(0, 100)
            ax.set_ylabel("Taxa de sucesso (%)")
            ax.set_title("Caso 2 — nenhuma transação (HTTP 403)")
            ax.text(0, 4, "0%", ha="center", color=cor, fontsize=16, weight="bold")
            save(fig, "fig-caso-02-taxa-sucesso.png")
            headers = ["#", "quando", "status", "T °C", "U %", "mensagem"]
            widths = [0.05, 0.14, 0.10, 0.08, 0.08, 0.55]

        body = amostras_body(rows, com_tx)
        mid = (len(body) + 1) // 2
        for faixa, chunk in (("1-15", body[:mid]), ("16-30", body[mid:])):
            fig = table_fig(
                headers,
                chunk,
                header_color=cor,
                figsize=(12.4, 5.6),
                fontsize=7.4,
                col_widths=widths,
                title=f"Caso {num} — amostras {faixa.replace('-', '–')} (n = 30)",
            )
            save(fig, f"tab-caso-0{num}-amostras-{faixa}.png")

    fig = table_fig(
        ["Métrica pedida no artigo", "O que os dados mostram"],
        [
            [
                "Latência de confirmação",
                "4 674 ms (caso 1), 4 384 ms (caso 3), 4 155 ms (caso 4); caso 2 sem tx",
            ],
            [
                "Custo em gás por atestação",
                "22 109 gas / 0,000221 IOTA (caso 1); 21 725 / 0,000217 (casos 3 e 4); 0 no caso 2",
            ],
            [
                "Tempo de envio (relay, não ESP32)",
                "1 638 ms (caso 1), 1 665 ms (caso 3), 1 482 ms (caso 4)",
            ],
            [
                "Taxa de sucesso no lote",
                "Com segurança: 100% limpo e 0% adulterado; sem segurança: 100% nos dois",
            ],
        ],
        figsize=(11.0, 2.8),
        fontsize=8.5,
        col_widths=[0.32, 0.68],
        title="Síntese para inserir no lugar do \\pendente",
    )
    save(fig, "tab-02-sintese-artigo.png")

    print(f"\n{len(list(OUT.glob('*.png')))} PNGs em {OUT}")


if __name__ == "__main__":
    main()
