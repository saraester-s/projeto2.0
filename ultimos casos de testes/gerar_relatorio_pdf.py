"""Relatório PDF dos 4 casos (lote 30) — um capítulo por teste."""

from __future__ import annotations

import csv
import math
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parent
CSV_DIR = ROOT / "csv"
PNG_DIR = ROOT / "graficos"
OUT = ROOT / "relatorio-quatro-casos.pdf"

T_CRIT_29 = 2.0452
A4 = (8.27, 11.69)
A4L = (11.69, 8.27)

C1, C2, C3, C4 = "#2563EB", "#DC2626", "#16A34A", "#EA580C"
COLORS = {"1": C1, "2": C2, "3": C3, "4": C4}


def br(v: float, nd: int = 2) -> str:
    s = f"{v:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def load(name: str) -> list[dict[str, str]]:
    with (CSV_DIR / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def floats(rows: list[dict[str, str]], key: str) -> list[float]:
    out: list[float] = []
    for row in rows:
        raw = (row.get(key) or "").strip()
        if raw:
            out.append(float(raw))
    return out


def stats(xs: list[float]) -> dict[str, float]:
    n = len(xs)
    if n == 0:
        return {"n": 0, "mean": 0, "std": 0, "ci_lo": 0, "ci_hi": 0, "mn": 0, "mx": 0}
    arr = np.array(xs, dtype=float)
    mean = float(arr.mean())
    std = float(arr.std(ddof=1)) if n > 1 else 0.0
    half = T_CRIT_29 * (std / math.sqrt(n)) if n else 0.0
    return {
        "n": n,
        "mean": mean,
        "std": std,
        "ci_lo": mean - half,
        "ci_hi": mean + half,
        "mn": float(arr.min()),
        "mx": float(arr.max()),
    }


def style() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 12,
            "axes.labelsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": True,
            "grid.alpha": 0.28,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
        }
    )


def header(fig, title: str, subtitle: str = "") -> None:
    fig.text(0.07, 0.965, title, fontsize=14, weight="bold", va="top", color="#111827")
    if subtitle:
        fig.text(0.07, 0.932, subtitle, fontsize=9, va="top", color="#4B5563")
    fig.add_artist(
        plt.Line2D([0.07, 0.93], [0.908, 0.908], transform=fig.transFigure, color="#D1D5DB", lw=0.8)
    )


def footer(fig, page: str) -> None:
    fig.text(
        0.07,
        0.025,
        "IC · atestação de firmware IoT · IOTA EVM Testnet · lote 30 · 27–29/10/2026",
        fontsize=7,
        color="#6B7280",
    )
    fig.text(0.93, 0.025, page, fontsize=7, color="#6B7280", ha="right")


def wrapped(ax, x, y, text: str, width: int = 108, **kwargs) -> None:
    ax.text(x, y, "\n".join(textwrap.wrap(text, width=width)), transform=ax.transAxes, **kwargs)


def paint_table(ax, headers: list[str], rows: list[list[str]], col_widths=None, header_color="#111827") -> None:
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=headers, loc="upper center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.35)
    if col_widths:
        for i, w in enumerate(col_widths):
            for r in range(len(rows) + 1):
                table[(r, i)].set_width(w)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#E5E7EB")
        if r == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", weight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#F9FAFB")


def page_capa(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=A4)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0.86), 1, 0.14, transform=ax.transAxes, color="#111827", clip_on=False))
    ax.text(0.07, 0.93, "Relatório experimental", color="white", fontsize=11, transform=ax.transAxes)
    ax.text(
        0.07,
        0.885,
        "Quatro casos de atestação de firmware",
        color="white",
        fontsize=18,
        weight="bold",
        transform=ax.transAxes,
    )
    ax.text(
        0.07,
        0.80,
        "ESP32 + DHT11 → relay Flask → contrato ESDRA na IOTA EVM Testnet",
        fontsize=10,
        color="#374151",
        transform=ax.transAxes,
    )
    ax.text(
        0.07,
        0.76,
        "Campanha de 27 a 29 de outubro de 2026 · 30 amostras por célula · intervalo ~10 s",
        fontsize=9,
        color="#6B7280",
        transform=ax.transAxes,
    )

    matrix = [
        ["", "Firmware limpo", "Firmware adulterado"],
        ["Com segurança\nPOST /atestar :5000", "Caso 1 — sucesso\n30/30 · HTTP 200", "Caso 2 — falha\n0/30 · HTTP 403"],
        ["Sem segurança\nPOST /leitura :5001", "Caso 3 — sucesso\n30/30 · HTTP 200", "Caso 4 — sucesso*\n30/30 · HTTP 200"],
    ]
    tax = fig.add_axes((0.08, 0.46, 0.84, 0.26))
    tax.axis("off")
    tbl = tax.table(cellText=matrix, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 3.2)
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

    notes = [
        "Contrato: ESDRA registrar  0xDAc95e767da4376456b132F4b78e18C0b8d0C669",
        "Hash enrolado (casos 1 e 2): 8422ebe7…d2ba28b6",
        "Adulteração (casos 2 e 4): Serial.println no .ino — hash 665704c9…1a84a275",
        "Gas price: 10 gwei. Assinatura EVM no PC (relay), não no ESP32.",
        "* Caso 4 “sucesso” = a chain aceitou a leitura; o firmware adulterado não foi barrado.",
    ]
    ax.text(0.07, 0.42, "Parâmetros comuns", fontsize=11, weight="bold", transform=ax.transAxes)
    ax.text(0.07, 0.38, "\n".join(notes), fontsize=8.5, color="#374151", transform=ax.transAxes, va="top", linespacing=1.7)
    ax.text(
        0.07,
        0.08,
        "Este PDF descreve cada teste: o que foi feito, os números do lote e o que o resultado mostra.",
        fontsize=9,
        color="#111827",
        transform=ax.transAxes,
    )
    footer(fig, "1")
    pdf.savefig(fig)
    plt.close(fig)


def page_comparacao(pdf: PdfPages, cases: dict) -> None:
    fig = plt.figure(figsize=A4)
    header(fig, "Comparação dos quatro casos", "Médias do lote de 30. Caso 2 não tem transação.")
    ax = fig.add_axes((0.05, 0.58, 0.90, 0.30))
    rows = [
        ["1", "com", "não", "200", "30/30", "1 638,23", "4 673,75", "22 109", "0,000221", "0,0066327"],
        ["2", "com", "sim", "403", "0/30", "—", "—", "—", "0", "0"],
        ["3", "sem", "não", "200", "30/30", "1 664,76", "4 384,17", "21 725", "0,000217", "0,0065175"],
        ["4", "sem", "sim", "200", "30/30", "1 481,69", "4 154,59", "21 725", "0,000217", "0,0065175"],
    ]
    paint_table(
        ax,
        ["Caso", "Seg.", "Adul.", "HTTP", "Tx", "Envio ms", "Conf. ms", "Gas", "IOTA/tx", "IOTA lote"],
        rows,
        header_color="#111827",
    )

    axb = fig.add_axes((0.08, 0.32, 0.84, 0.22))
    labels = ["Caso 1", "Caso 2", "Caso 3", "Caso 4"]
    vals = [30, 0, 30, 30]
    bars = axb.bar(labels, vals, color=[C1, C2, C3, C4], width=0.55)
    axb.set_ylabel("leituras aceitas")
    axb.set_title("Taxa de aceite (HTTP 200 + transação)")
    axb.set_ylim(0, 38)
    for b, v in zip(bars, vals):
        axb.text(b.get_x() + b.get_width() / 2, v + 0.6, str(v), ha="center", fontsize=9, weight="bold")

    axn = fig.add_axes((0.07, 0.06, 0.86, 0.22))
    axn.axis("off")
    texto = (
        "Leitura. Só o caso 2 é recusado: a allowlist do relay barra o hash adulterado "
        "antes de chamar o contrato. Sem allowlist (casos 3 e 4) a adulteração grava na "
        "cadeia igual ao firmware limpo — mesmo gas (21 725) e mesmo custo (0,000217 IOTA). "
        "O overhead de atestação no envio é pequeno neste lote (1 638 ms no caso 1 vs 1 665 ms "
        "no caso 3). A confirmação on-chain fica na faixa de 4–5 s e depende do bloco, não do "
        "filtro de hash. Não há medição de tempo de assinatura no ESP32: a chave EVM assina no PC."
    )
    wrapped(axn, 0, 0.95, texto, width=115, va="top", fontsize=9, color="#111827")
    footer(fig, "2")
    pdf.savefig(fig)
    plt.close(fig)

    fig = plt.figure(figsize=A4)
    header(fig, "Gráficos comparativos", "Azul = 1 · vermelho = 2 · verde = 3 · laranja = 4")
    gs = fig.add_gridspec(2, 1, left=0.10, right=0.93, top=0.88, bottom=0.08, hspace=0.32)

    envio = [
        cases["1"]["envio"]["mean"] if cases["1"]["envio"]["n"] else 0,
        0,
        cases["3"]["envio"]["mean"],
        cases["4"]["envio"]["mean"],
    ]
    conf = [
        cases["1"]["conf"]["mean"] if cases["1"]["conf"]["n"] else 0,
        0,
        cases["3"]["conf"]["mean"],
        cases["4"]["conf"]["mean"],
    ]
    ax1 = fig.add_subplot(gs[0])
    x = np.arange(4)
    w = 0.36
    b1 = ax1.bar(x - w / 2, envio, w, color="#93C5FD", label="envio")
    b2 = ax1.bar(x + w / 2, conf, w, color=[C1, C2, C3, C4], label="confirmação")
    ax1.set_xticks(x, labels)
    ax1.set_ylabel("ms")
    ax1.set_title("Tempo médio de envio e de confirmação on-chain")
    ax1.legend(frameon=False)
    ax1.text(1, 120, "n/a", ha="center", color=C2, fontsize=9)
    for b in list(b1) + list(b2):
        h = b.get_height()
        if h > 0:
            ax1.text(b.get_x() + b.get_width() / 2, h, f"{h:.0f}", ha="center", va="bottom", fontsize=7)

    ax2 = fig.add_subplot(gs[1])
    custo = [0.0066327, 0.0, 0.0065175, 0.0065175]
    bars = ax2.bar(labels, custo, color=[C1, C2, C3, C4], width=0.55)
    ax2.set_ylabel("IOTA (lote)")
    ax2.set_title("Custo total do lote de 30")
    for b, v in zip(bars, custo):
        ax2.text(b.get_x() + b.get_width() / 2, v, f"{br(v, 7)}", ha="center", va="bottom", fontsize=8)
    footer(fig, "3")
    pdf.savefig(fig)
    plt.close(fig)

    fig = plt.figure(figsize=A4)
    header(fig, "Séries temporais (só quem gerou transação)", "Caso 2 não entra: HTTP 403, sem tx.")
    gs = fig.add_gridspec(2, 1, left=0.10, right=0.93, top=0.88, bottom=0.08, hspace=0.32)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    for key, color, lab in (("1", C1, "Caso 1"), ("3", C3, "Caso 3"), ("4", C4, "Caso 4")):
        xs = np.arange(1, len(cases[key]["envio_s"]) + 1)
        ax1.plot(xs, cases[key]["envio_s"], color=color, lw=1.6, marker="o", ms=3, label=lab)
        ax2.plot(xs, cases[key]["conf_s"], color=color, lw=1.6, marker="o", ms=3, label=lab)
    ax1.set_title("Tempo de envio por amostra")
    ax1.set_ylabel("ms")
    ax1.legend(frameon=False, ncol=3)
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax2.set_title("Tempo de confirmação on-chain por amostra")
    ax2.set_xlabel("amostra do lote")
    ax2.set_ylabel("ms")
    ax2.legend(frameon=False, ncol=3)
    ax2.xaxis.set_major_locator(MaxNLocator(integer=True))
    footer(fig, "4")
    pdf.savefig(fig)
    plt.close(fig)


def page_caso(
    pdf: PdfPages,
    *,
    num: str,
    titulo: str,
    cor: str,
    ficha: list[tuple[str, str]],
    leitura: str,
    rows: list[dict[str, str]],
    envio_s: list[float],
    conf_s: list[float],
    gas_s: list[float],
    st_envio,
    st_conf,
    st_gas,
    page_a: str,
    page_b: str,
    page_c: str,
    page_d: str,
) -> None:
    fig = plt.figure(figsize=A4)
    header(fig, f"Caso {num} — {titulo}", "Ficha do experimento e médias do lote 30")
    ax = fig.add_axes((0.08, 0.58, 0.84, 0.30))
    paint_table(ax, ["Campo", "Valor"], [[a, b] for a, b in ficha], col_widths=[0.32, 0.68], header_color=cor)

    axm = fig.add_axes((0.08, 0.30, 0.84, 0.24))
    if st_envio["n"]:
        metricas = [
            ["Envio (ms)", br(st_envio["mean"]), br(st_envio["std"]), f"[{br(st_envio['ci_lo'])} ; {br(st_envio['ci_hi'])}]", f"{br(st_envio['mn'])}–{br(st_envio['mx'])}"],
            ["Confirmação (ms)", br(st_conf["mean"]), br(st_conf["std"]), f"[{br(st_conf['ci_lo'])} ; {br(st_conf['ci_hi'])}]", f"{br(st_conf['mn'])}–{br(st_conf['mx'])}"],
            ["Gas por tx", br(st_gas["mean"], 0), br(st_gas["std"], 0), f"[{br(st_gas['ci_lo'], 0)} ; {br(st_gas['ci_hi'], 0)}]", br(st_gas["mean"], 0)],
        ]
    else:
        metricas = [
            ["Envio (ms)", "—", "—", "—", "sem transação"],
            ["Confirmação (ms)", "—", "—", "—", "sem transação"],
            ["Gas por tx", "—", "—", "—", "sem transação"],
        ]
    paint_table(
        axm,
        ["Métrica", "Média", "s", "IC 95% (t, gl=29)", "min–máx"],
        metricas,
        header_color=cor,
    )

    axn = fig.add_axes((0.07, 0.05, 0.86, 0.16))
    axn.axis("off")
    axn.text(0, 0.95, "O que este resultado mostra", fontsize=10, weight="bold", transform=axn.transAxes, va="top")
    wrapped(axn, 0, 0.72, leitura, width=112, va="top", fontsize=8.5, color="#111827")
    footer(fig, page_a)
    pdf.savefig(fig)
    plt.close(fig)

    fig = plt.figure(figsize=A4)
    header(fig, f"Caso {num} — séries do lote", "n = 30 amostras sequenciais")
    if envio_s:
        gs = fig.add_gridspec(3, 1, left=0.12, right=0.93, top=0.88, bottom=0.08, hspace=0.38)
        series = [
            (envio_s, "Tempo de envio da transação (relay)", "ms"),
            (conf_s, "Latência de confirmação on-chain", "ms"),
            (gas_s, "Gas usado por transação", "gas"),
        ]
        for i, (vals, title, ylab) in enumerate(series):
            ax = fig.add_subplot(gs[i])
            xs = np.arange(1, len(vals) + 1)
            ax.plot(xs, vals, color=cor, lw=1.7, marker="o", ms=3.5)
            ax.axhline(float(np.mean(vals)), color="#6B7280", ls="--", lw=0.9, label="média")
            ax.set_title(title)
            ax.set_ylabel(ylab)
            ax.legend(frameon=False, loc="upper right")
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            if i == 2:
                ax.set_xlabel("amostra")
    else:
        ax = fig.add_axes((0.12, 0.35, 0.76, 0.40))
        ax.bar(["Firmware adulterado"], [0], color=cor, width=0.4)
        ax.set_ylim(0, 100)
        ax.set_ylabel("taxa de sucesso (%)")
        ax.set_title("Nenhuma transação — 30 rejeições HTTP 403")
        ax.text(0, 4, "0%", ha="center", color=cor, fontsize=16, weight="bold")
        axn = fig.add_axes((0.08, 0.08, 0.84, 0.20))
        axn.axis("off")
        wrapped(
            axn,
            0,
            0.9,
            "O gráfico de latência e de gás não se aplica: o relay recusou o hash antes de montar a transação. "
            "Temperatura e umidade do DHT11 chegaram (24,9–25,0 °C; 67–68 %), mas não foram gravadas na chain.",
            width=110,
            va="top",
            fontsize=9,
        )
    footer(fig, page_b)
    pdf.savefig(fig)
    plt.close(fig)

    if envio_s:
        headers = ["#", "quando", "status", "envio ms", "conf. ms", "gas", "IOTA", "T °C", "U %", "tx"]
        body = []
        for i, r in enumerate(rows, 1):
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
        widths = [0.04, 0.14, 0.08, 0.09, 0.09, 0.07, 0.10, 0.07, 0.07, 0.15]
    else:
        headers = ["#", "quando", "status", "T °C", "U %", "mensagem"]
        body = []
        for i, r in enumerate(rows, 1):
            msg = r.get("mensagem") or ""
            if len(msg) > 78:
                msg = msg[:75] + "…"
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
        widths = [0.05, 0.16, 0.10, 0.08, 0.08, 0.53]

    mid = (len(body) + 1) // 2
    chunks = [("1–15", body[:mid]), ("16–30", body[mid:])]
    for extra, (faixa, chunk) in enumerate(chunks):
        fig = plt.figure(figsize=A4L)
        header(
            fig,
            f"Caso {num} — amostras brutas {faixa} (n = {len(rows)})",
            "CSV do lote · paisagem para caber as colunas",
        )
        ax = fig.add_axes((0.04, 0.08, 0.92, 0.80))
        paint_table(ax, headers, chunk, col_widths=widths, header_color=cor)
        ax.tables[0].set_fontsize(7.2)
        ax.tables[0].scale(1, 1.45)
        footer(fig, page_c if extra == 0 else page_d)
        pdf.savefig(fig)
        plt.close(fig)


def page_conclusao(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=A4)
    header(fig, "Síntese para o texto da IC", "Como usar estes números no lugar do \\pendente")
    ax = fig.add_axes((0.07, 0.08, 0.86, 0.80))
    ax.axis("off")
    blocos = [
        (
            "Latência de confirmação",
            "A média ficou em 4 674 ms (caso 1), 4 384 ms (caso 3) e 4 155 ms (caso 4). "
            "A allowlist não é o termo dominante: a espera é a do bloco na testnet. "
            "O caso 2 não tem latência porque a transação nunca sai.",
        ),
        (
            "Custo em gás por atestação",
            "Caso 1: 22 109 gas e 0,000221 IOTA por tx (0,0066327 no lote). "
            "Casos 3 e 4: 21 725 gas e 0,000217 IOTA por tx (0,0065175 no lote). "
            "A diferença de gas entre com e sem atestação neste lote é pequena (~384 unidades) "
            "porque os dois caminhos chamam o mesmo contrato registrar. O caso 2 custa zero.",
        ),
        (
            "Tempo de envio no relay (não é assinatura no ESP32)",
            "Médias: 1 638 ms (caso 1), 1 665 ms (caso 3), 1 482 ms (caso 4). "
            "Não há série de tempo de assinatura no chip: o ESP32 só faz POST HTTP; "
            "a carteira EVM assina no computador do relay.",
        ),
        (
            "Taxa de sucesso (lote sequencial, não carga)",
            "Com segurança: 100% no firmware limpo e 0% no adulterado. "
            "Sem segurança: 100% nos dois. Intervalo ~10 s — isto mede o filtro de hash, "
            "não throughput sob stress.",
        ),
        (
            "Conclusão experimental",
            "A atestação só é efetiva quando a allowlist está ligada. Sem ela, firmware limpo "
            "e adulterado são indistinguíveis on-chain (mesmo gas, mesmo HTTP 200, mesmo custo).",
        ),
    ]
    y = 0.98
    for titulo, corpo in blocos:
        ax.text(0, y, titulo, fontsize=11, weight="bold", va="top", transform=ax.transAxes, color="#111827")
        y -= 0.045
        wrapped(ax, 0, y, corpo, width=108, va="top", fontsize=9, color="#374151")
        y -= 0.13
    footer(fig, "21")
    pdf.savefig(fig)
    plt.close(fig)


def main() -> None:
    style()
    c1 = load("caso-01-com-seguranca-sem-adulteracao.csv")
    c2 = load("caso-02-com-seguranca-adulteracao.csv")
    c3 = load("caso-03-sem-seguranca-sem-adulteracao.csv")
    c4 = load("caso-04-sem-seguranca-adulteracao.csv")

    def pack(rows):
        e, c, g = floats(rows, "tempo_envio_ms"), floats(rows, "tempo_confirmacao_ms"), floats(rows, "gas_usado")
        return {
            "rows": rows,
            "envio_s": e,
            "conf_s": c,
            "gas_s": g,
            "envio": stats(e),
            "conf": stats(c),
            "gas": stats(g),
        }

    cases = {"1": pack(c1), "2": pack(c2), "3": pack(c3), "4": pack(c4)}

    with PdfPages(OUT) as pdf:
        page_capa(pdf)
        page_comparacao(pdf, cases)

        page_caso(
            pdf,
            num="1",
            titulo="com segurança, sem adulteração → sucesso",
            cor=C1,
            ficha=[
                ("Segurança", "com — src/, POST /atestar :5000"),
                ("Adulteração", "não"),
                ("Resultado", "sucesso · HTTP 200 + tx_hash · 30/30"),
                ("Quando", "2026-10-27 17:05:53 → 2026-10-29 15:56:14"),
                ("Hash enrolado", "8422ebe782c2f51ab17c330621d0b4c2c29db4175a82929fec0bab04d2ba28b6"),
                ("Custo médio / total", "0,000221 IOTA  ·  0,0066327 IOTA no lote"),
            ],
            leitura=(
                "O firmware limpo passa na allowlist e todas as 30 leituras viram transação. "
                "Confirmação média 4 674 ms (IC 95% da média no gráfico da ficha). "
                "Este é o caminho feliz da atestação: o hash bate, o contrato registra, há custo de gas."
            ),
            rows=c1,
            envio_s=cases["1"]["envio_s"],
            conf_s=cases["1"]["conf_s"],
            gas_s=cases["1"]["gas_s"],
            st_envio=cases["1"]["envio"],
            st_conf=cases["1"]["conf"],
            st_gas=cases["1"]["gas"],
            page_a="5",
            page_b="6",
            page_c="7",
            page_d="8",
        )
        page_caso(
            pdf,
            num="2",
            titulo="com segurança, adulteração → falha",
            cor=C2,
            ficha=[
                ("Segurança", "com — src/, POST /atestar :5000"),
                ("Adulteração", "sim — Serial.println no .ino"),
                ("Resultado", "falha · HTTP 403 · 0 transações"),
                ("Quando", "2026-10-29 16:12:29 → 16:17:24"),
                ("Hash enrolado", "8422ebe7…d2ba28b6"),
                ("Hash apresentado", "665704c91f218e2e3f8b13c595ec15898215f4b9ed65af0664448c7e1a84a275"),
                ("Mensagem", "Hash de firmware nao enrolado. Codigo alterado nao e aceito."),
                ("DHT11", "24,9–25,0 °C · umidade 67–68 %"),
            ],
            leitura=(
                "Único caso em que a segurança funciona como filtro. O sensor continua medindo, "
                "mas o relay recusa o hash e não chama o contrato. Custo 0, latência on-chain inexistente. "
                "Compara diretamente com o caso 4: a mesma adulteração, sem allowlist, grava na chain."
            ),
            rows=c2,
            envio_s=[],
            conf_s=[],
            gas_s=[],
            st_envio=cases["2"]["envio"],
            st_conf=cases["2"]["conf"],
            st_gas=cases["2"]["gas"],
            page_a="9",
            page_b="10",
            page_c="11",
            page_d="12",
        )
        page_caso(
            pdf,
            num="3",
            titulo="sem segurança, sem adulteração → sucesso",
            cor=C3,
            ficha=[
                ("Segurança", "sem — sem_atestacao/, POST /leitura :5001"),
                ("Adulteração", "não"),
                ("Resultado", "sucesso · HTTP 200 + tx_hash · 30/30"),
                ("Quando", "2026-10-29 16:42:11 → 16:49:23"),
                ("Hash on-chain", "zeros (HASH_SEM_ATESTACAO); relay sem allowlist"),
                ("DHT11", "25,2–25,3 °C · umidade 66 %"),
                ("Custo médio / total", "0,000217 IOTA  ·  0,0065175 IOTA no lote"),
            ],
            leitura=(
                "Baseline sem atestação e com firmware limpo. Gas constante 21 725. "
                "Tempos de envio e confirmação na mesma ordem de grandeza do caso 1: "
                "tirar o filtro de hash não acelera a chain de forma material neste lote."
            ),
            rows=c3,
            envio_s=cases["3"]["envio_s"],
            conf_s=cases["3"]["conf_s"],
            gas_s=cases["3"]["gas_s"],
            st_envio=cases["3"]["envio"],
            st_conf=cases["3"]["conf"],
            st_gas=cases["3"]["gas"],
            page_a="13",
            page_b="14",
            page_c="15",
            page_d="16",
        )
        page_caso(
            pdf,
            num="4",
            titulo="sem segurança, adulteração → sucesso (falso negativo)",
            cor=C4,
            ficha=[
                ("Segurança", "sem — sem_atestacao/, POST /leitura :5001"),
                ("Adulteração", "sim — o mesmo Serial.println do caso 2"),
                ("Resultado", "sucesso HTTP 200 — a chain NÃO detecta a adulteração"),
                ("Quando", "2026-10-29 17:02:38 → 17:09:33"),
                ("Hash on-chain", "zeros; ninguém confere firmware"),
                ("DHT11", "25,1–25,2 °C · umidade 66 %"),
                ("Custo médio / total", "0,000217 IOTA  ·  0,0065175 IOTA no lote (idêntico ao caso 3)"),
            ],
            leitura=(
                "Mesma adulteração do caso 2, mas sem allowlist: 30/30 transações, mesmo gas e mesmo "
                "custo do firmware limpo. É o contraexemplo da pesquisa — a blockchain registra a "
                "leitura, não a integridade do código, se o relay não filtrar o hash."
            ),
            rows=c4,
            envio_s=cases["4"]["envio_s"],
            conf_s=cases["4"]["conf_s"],
            gas_s=cases["4"]["gas_s"],
            st_envio=cases["4"]["envio"],
            st_conf=cases["4"]["conf"],
            st_gas=cases["4"]["gas"],
            page_a="17",
            page_b="18",
            page_c="19",
            page_d="20",
        )
        page_conclusao(pdf)

    print(f"PDF gerado: {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
