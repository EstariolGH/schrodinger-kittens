"""
Коты Шрёдингера: кот, кошка и котёнок.

  кот     умирает, если банка разбита
  кошка   умирает, если банка цела            (противоположные условия)
  котёнок рождается, только если оба родителя живы

Режимы:
  shared       один общий атом с банкой (котёнок невозможен)
  independent  у каждого кота свой атом (котёнок рождается с некоторой вероятностью)

Запуск:
  python cats.py                              общий атом, симулятор
  python cats.py --mode independent           у каждого свой атом
  python cats.py --theta 60                   атом «распадается» с другой вероятностью
  python cats.py --backend fake               модель шумного чипа IBM (без очереди)
  python cats.py --backend ibm                самый свободный настоящий квантовый компьютер IBM
  python cats.py --backend ibm --chip ibm_fez конкретный процессор

Перед запуском на IBM один раз сохраните ключ:  python save_key.py
"""

import argparse
import math
import sys

# чтобы русский текст не ломался в консоли Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, transpile
from qiskit.quantum_info import Statevector, partial_trace

# --------------------------------------------------------------------------
# 1. Схема
# --------------------------------------------------------------------------

def build_circuit(mode: str, theta_deg: float) -> QuantumCircuit:
    """Схема без измерений: кубиты 0-2 — коты, дальше — банки."""
    theta = math.radians(theta_deg)
    cat = QuantumRegister(1, "кот")
    she = QuantumRegister(1, "кошка")
    kit = QuantumRegister(1, "котёнок")
    vial_a = QuantumRegister(1, "банка_А")
    regs = [cat, she, kit, vial_a]
    if mode == "independent":
        vial_b = QuantumRegister(1, "банка_Б")
        regs.append(vial_b)
    qc = QuantumCircuit(*regs)

    qc.x(cat)                       # кот жив
    qc.x(she)                       # кошка жива
    qc.ry(theta, vial_a)            # атом А: распался / не распался (90° = поровну)

    if mode == "shared":
        qc.cx(vial_a, cat)                    # банка разбита  -> кот умирает
        qc.cx(vial_a, she, ctrl_state=0)      # банка цела     -> кошка умирает
    else:
        qc.ry(theta, vial_b)                  # атом Б, независимый
        qc.cx(vial_a, cat)                    # банка А разбита -> кот умирает
        qc.cx(vial_b, she)                    # банка Б разбита -> кошка умирает

    qc.ccx(cat, she, kit)           # оба живы -> котёнок рождается
    return qc


def with_measurements(qc: QuantumCircuit) -> QuantumCircuit:
    """Измеряем только котов: кот -> бит 0, кошка -> бит 1, котёнок -> бит 2."""
    m = qc.copy()
    creg = ClassicalRegister(3, "c")
    m.add_register(creg)
    m.measure([0, 1, 2], creg)
    return m

# --------------------------------------------------------------------------
# 2. Подглядываем в закрытую коробку (только на симуляторе!)
# --------------------------------------------------------------------------

def describe(bits3: str) -> str:
    """'abc' (котёнок, кошка, кот — порядок Qiskit) -> человеческая подпись."""
    kit, she, cat = bits3
    return (f"кот {'жив' if cat == '1' else 'мёртв'}\n"
            f"кошка {'жива' if she == '1' else 'мертва'}\n"
            f"котёнок {'есть' if kit == '1' else 'нет'}")


def peek_into_box(qc: QuantumCircuit) -> None:
    sv = Statevector(qc)
    n = qc.num_qubits
    print("\n=== Коробка ещё закрыта: полное состояние ===")
    for bits, p in sorted(sv.probabilities_dict().items()):
        if p < 1e-9:
            continue
        amp = sv.data[int(bits, 2)]
        story = describe(bits[-3:]).replace("\n", ", ")
        vials = bits[:-3][::-1]               # банки: А, (Б)
        vial_txt = ", ".join(f"банка_{'АБ'[i]} {'разбита' if b == '1' else 'цела'}"
                             for i, b in enumerate(vials))
        print(f"  амплитуда {amp.real:+.3f}   P = {p:.3f}   {story}  |  {vial_txt}")

    print("\n=== Каждый по отдельности (матрица плотности) ===")
    for idx, name in [(0, "кот"), (1, "кошка"), (2, "котёнок")]:
        rho = partial_trace(sv, [i for i in range(n) if i != idx])
        p_alive = rho.data[1, 1].real
        purity = rho.purity().real
        kind = "чистое состояние" if purity > 0.999 else "смесь (запутан с остальными)"
        print(f"  {name:8s}: жив с вероятностью {p_alive:.3f},  чистота {purity:.3f}  — {kind}")

# --------------------------------------------------------------------------
# 3. Открываем коробку: запуск
# --------------------------------------------------------------------------

def run(qc_meas: QuantumCircuit, backend_name: str, shots: int, chip: str | None) -> tuple[dict, str]:
    if backend_name == "sim":
        from qiskit_aer import AerSimulator
        sim = AerSimulator()
        counts = sim.run(transpile(qc_meas, sim), shots=shots).result().get_counts()
        return counts, "идеальный симулятор"

    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_ibm_runtime.executor_sampler import Sampler

    if backend_name == "fake":
        from qiskit_ibm_runtime.fake_provider import FakeTorino
        backend = FakeTorino()
        title = "модель шумного чипа FakeTorino"
    else:
        from qiskit_ibm_runtime import QiskitRuntimeService
        from qiskit_ibm_runtime.accounts.exceptions import AccountNotFoundError
        try:
            service = QiskitRuntimeService()
        except AccountNotFoundError:
            sys.exit("\nКлюч IBM не найден. Сначала один раз выполните:  python save_key.py\n"
                     "(подробности — в README, раздел «Ключ IBM»)")
        backend = (service.backend(chip) if chip
                   else service.least_busy(operational=True, simulator=False))
        title = f"квантовый компьютер {backend.name}"
        print(f"\nОтправляю на {backend.name}, ждём очередь...")
        print("(Очередь бывает от минуты до пары часов. Окно можно не закрывать —\n"
              " результат придёт сам. Статус задачи видно на quantum.cloud.ibm.com → Workloads.)")

    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    job = Sampler(mode=backend).run([pm.run(qc_meas)], shots=shots)
    if backend_name == "ibm":
        print("Job ID:", job.job_id())
    counts = job.result()[0].data.c.get_counts()
    return counts, title


def plot(counts: dict, shots: int, title: str, filename: str, show: bool) -> None:
    all_keys = [format(i, "03b") for i in range(8)]
    values = [counts.get(k, 0) for k in all_keys]
    labels = [describe(k) for k in all_keys]
    colors = ["#1D9E75" if k[0] == "1" else "#7F77DD" for k in all_keys]

    fig, ax = plt.subplots(figsize=(13, 5.5))
    bars = ax.bar(range(8), values, color=colors)
    for b, v in zip(bars, values):
        if v:
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v}\n({v / shots:.0%})",
                    ha="center", va="bottom", fontsize=9)
    ax.set_xticks(range(8))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("сколько раз выпало")
    ax.set_ylim(0, max(values) * 1.2 + 1)
    ax.set_title(f"Коты Шрёдингера — {title}, {shots} запусков")
    ax.spines[["top", "right"]].set_visible(False)
    born = sum(v for k, v in zip(all_keys, values) if k[0] == "1")
    ax.text(0.99, 0.97, f"котёнок родился: {born / shots:.1%}",
            transform=ax.transAxes, ha="right", va="top", fontsize=11,
            color="#0F6E56" if born else "#534AB7")
    fig.tight_layout()
    fig.savefig(filename, dpi=130)
    print(f"\nГистограмма сохранена в {filename}")
    if show:
        plt.show()

# --------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Коты Шрёдингера на квантовом компьютере")
    ap.add_argument("--mode", choices=["shared", "independent"], default="shared",
                    help="shared — общий атом, independent — у каждого свой")
    ap.add_argument("--theta", type=float, default=90.0,
                    help="угол Ry для атома в градусах (90 = распад 50/50)")
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--backend", choices=["sim", "fake", "ibm"], default="sim")
    ap.add_argument("--chip", default=None, help="имя чипа IBM, например ibm_fez")
    ap.add_argument("--out", default="cats_histogram.png")
    ap.add_argument("--no-show", action="store_true", help="не открывать окно с графиком")
    args = ap.parse_args()

    qc = build_circuit(args.mode, args.theta)
    print(f"Режим: {'общий атом' if args.mode == 'shared' else 'у каждого свой атом'}, "
          f"угол атома {args.theta}°")
    print(qc.draw(output="text", fold=-1))

    peek_into_box(qc)

    counts, title = run(with_measurements(qc), args.backend, args.shots, args.chip)
    print("\n=== Коробку открыли ===")
    for bits, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {c:5d} раз:  {describe(bits).replace(chr(10), ', ')}")

    plot(counts, args.shots, title, args.out, show=not args.no_show)


if __name__ == "__main__":
    main()
