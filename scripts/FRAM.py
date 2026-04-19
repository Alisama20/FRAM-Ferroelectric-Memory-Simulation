"""
==========================================================================
 Simulación de una celda FRAM con el modelo de Landau-Khalatnikov
==========================================================================

 Genera 3 figuras interactivas:
   1. Energía libre de Landau + Histéresis P-E
   2. Operación completa de celda FRAM (Write → Wait → Read)
   3. Transición de fase Pr(T)

 Modelo:
   G(P) = α·P² + β·P⁴ − E·P          (energía libre de Landau-Devonshire)
   ρ·dP/dt = −dG/dP = E − 2αP − 4βP³  (dinámica de Landau-Khalatnikov)
   i(t) = A · dP/dt                    (corriente medida por el circuito)

 Referencias:
   [1] A.F. Devonshire, "Theory of barium titanate", Phil. Mag. 40, 1040 (1949)
   [2] L. Landau & I. Khalatnikov, Dokl. Akad. Nauk SSSR 96, 469 (1954)
   [3] M. Pešić et al., J. Comput. Electron. (2017) — parámetros HfO₂
==========================================================================
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# =====================================================================
# PARÁMETROS FÍSICOS — modificar aquí para explorar
# =====================================================================
Pr_phys = 20       # Polarización remanente (µC/cm²) — típico HfO₂: 10-25
Ec_phys = 1.5      # Campo coercitivo (MV/cm) — típico HfO₂: 1-2
d_nm    = 10       # Espesor de la capa ferroeléctrica (nm) — típico: 5-20
Tc      = 450      # Temperatura de Curie (K) — típico HfO₂: 400-500
# =====================================================================

Vc_phys = Ec_phys * d_nm / 10  # Voltaje coercitivo (V) = Ec × d

print("=" * 60)
print(" SIMULACIÓN FRAM — Modelo de Landau-Khalatnikov")
print("=" * 60)
print(f"  Pr  = {Pr_phys} µC/cm²")
print(f"  Ec  = {Ec_phys} MV/cm")
print(f"  d   = {d_nm} nm")
print(f"  Vc  = {Vc_phys:.2f} V")
print(f"  Tc  = {Tc} K")
print("=" * 60)

# --- Parámetros normalizados (adimensionales para estabilidad numérica) ---
# G(p) = a·p² + b·p⁴   con a = -1, b = 1
# → p₀ = 1/√2 ≈ 0.707,  ec = 2/(3√3) ≈ 0.385
a = -1.0
b = 1.0
p0 = np.sqrt(-a / (2 * b))          # polarización espontánea normalizada
ec = (2/3) * np.sqrt(-a**3 / (6*b)) # campo coercitivo normalizado

def dGdp(p, e):
    """Derivada de la energía libre: dG/dp = 2a·p + 4b·p³ - e"""
    return 2*a*p + 4*b*p**3 - e


# =====================================================================
# FIGURA 1: Energía libre + Histéresis P-E
# =====================================================================
print("\n[1/3] Calculando energía libre e histéresis P-E...")

# --- Panel izquierdo: G(P) para distintos campos ---
pp = np.linspace(-1.2, 1.2, 500)

# --- Panel derecho: Histéresis dinámica ---
dt = 0.005
n_steps = 40000
emax = 1.0  # amplitud del campo (en unidades de ec)

t = np.arange(n_steps) * dt
period = n_steps * dt / 2
e_t = emax * (2 * np.abs(2 * (t / period - np.floor(t / period + 0.5))) - 1)

p_hyst = np.zeros(n_steps)
p_hyst[0] = -p0

for i in range(1, n_steps):
    dpdt = -dGdp(p_hyst[i-1], e_t[i])
    p_hyst[i] = np.clip(p_hyst[i-1] + dpdt * dt, -1.5, 1.5)

# --- Dibujar ---
fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fig1.suptitle("Modelo de Landau-Devonshire aplicado a FRAM", fontsize=14, fontweight='bold')

# Energía libre
for ef, ls, lbl, col in [(0, '-', 'E = 0 (reposo)', '#0F2B46'),
                          (1.2*ec, '--', 'E > Ec (escritura →)', '#E8963E'),
                          (-1.2*ec, ':', 'E < −Ec (← escritura)', '#1A5276')]:
    G = a * pp**2 + b * pp**4 - ef * pp
    ax1.plot(pp / p0 * Pr_phys, G, ls, color=col, lw=2.5, label=lbl)

ax1.set_xlabel('Polarización P (µC/cm²)')
ax1.set_ylabel('Energía libre G (u.a.)')
ax1.set_title('Energía libre de Landau')
ax1.legend()
ax1.axhline(0, color='gray', lw=0.3)
ax1.axvline(0, color='gray', lw=0.3)
ax1.annotate('Bit "0"\n−Pr', xy=(-Pr_phys, -0.28), fontsize=11,
             color='#1A5276', ha='center', fontweight='bold')
ax1.annotate('Bit "1"\n+Pr', xy=(Pr_phys, -0.28), fontsize=11,
             color='#E8963E', ha='center', fontweight='bold')

# Histéresis (segundo ciclo, sin transitorio inicial)
half = len(t) // 2
ax2.plot(e_t[half:] / ec, p_hyst[half:] / p0 * Pr_phys, color='#E8963E', lw=2.5)
ax2.set_xlabel('Campo E / Ec (adimensional)')
ax2.set_ylabel('Polarización P (µC/cm²)')
ax2.set_title('Histéresis P-E simulada (Landau-Khalatnikov)')
ax2.axhline(0, color='gray', lw=0.3)
ax2.axvline(0, color='gray', lw=0.3)
ax2.annotate(f'+Pr = {Pr_phys}', xy=(0.1, Pr_phys * 0.9), fontsize=11,
             color='#E8963E', fontweight='bold')
ax2.annotate(f'−Pr = {-Pr_phys}', xy=(0.1, -Pr_phys * 0.9), fontsize=11,
             color='#1A5276', fontweight='bold')
ax2.text(0.97, 0.05, 'G = αP² + βP⁴ − EP\nρ·dP/dt = −dG/dP',
         transform=ax2.transAxes, fontsize=10, ha='right', va='bottom',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEF9E7',
                   edgecolor='#E8963E', lw=1.5))

fig1.tight_layout()
fig1.savefig("../figures/landau_hysteresis.png", dpi=150, bbox_inches="tight")
print("  ✓ Figura 1 lista")


# =====================================================================
# FIGURA 2: Operación FRAM completa (Write → Wait → Read)
# =====================================================================
print("[2/3] Simulando operación Write → Wait → Read...")

dt2 = 0.002
t_wr = 30.0     # duración escritura (u.a.)
t_wait = 60.0   # espera sin voltaje
t_rd = 30.0     # duración lectura
t_tot = t_wr + t_wait + t_rd + 20
n2 = int(t_tot / dt2)
t2 = np.arange(n2) * dt2

# Secuencia de voltajes
e2 = np.zeros(n2)
e_write = -1.0   # campo negativo → escribir bit "0"
e_read = 1.0     # campo positivo → leer
ramp = 3.0       # duración de la rampa (u.a.)

for i in range(n2):
    ti = t2[i]
    if ti < ramp:
        e2[i] = e_write * ti / ramp
    elif ti < t_wr - ramp:
        e2[i] = e_write
    elif ti < t_wr:
        e2[i] = e_write * (1 - (ti - t_wr + ramp) / ramp)
    elif ti < t_wr + t_wait:
        e2[i] = 0
    elif ti < t_wr + t_wait + ramp:
        e2[i] = e_read * (ti - t_wr - t_wait) / ramp
    elif ti < t_wr + t_wait + t_rd - ramp:
        e2[i] = e_read
    elif ti < t_wr + t_wait + t_rd:
        e2[i] = e_read * (1 - (ti - t_wr - t_wait - t_rd + ramp) / ramp)

# Simular desde bit "1" (p = +p0)
p2_1 = np.zeros(n2)
p2_1[0] = p0
i2_1 = np.zeros(n2)
for i in range(1, n2):
    dpdt = -dGdp(p2_1[i-1], e2[i])
    p2_1[i] = np.clip(p2_1[i-1] + dpdt * dt2, -1.5, 1.5)
    i2_1[i] = dpdt

# Simular desde bit "0" (p = -p0)
p2_0 = np.zeros(n2)
p2_0[0] = -p0
i2_0 = np.zeros(n2)
for i in range(1, n2):
    dpdt = -dGdp(p2_0[i-1], e2[i])
    p2_0[i] = np.clip(p2_0[i-1] + dpdt * dt2, -1.5, 1.5)
    i2_0[i] = dpdt

# Convertir a unidades físicas para los ejes
t_ns = t2 * 0.5   # escala temporal ≈ 0.5 ns por unidad

# --- Dibujar ---
fig2, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
fig2.suptitle("Operación completa de celda FRAM (simulación Landau-Khalatnikov)",
              fontsize=14, fontweight='bold')

# Panel 1: Voltaje
ax = axes[0]
ax.fill_between(t_ns, e2 / ec * Vc_phys, alpha=0.12, color='#1A5276')
ax.plot(t_ns, e2 / ec * Vc_phys, color='#1A5276', lw=2)
ax.set_ylabel('Voltaje (V)')
ax.axhline(0, color='gray', lw=0.3)
ax.axhline(Vc_phys, color='#C0392B', ls=':', lw=1, alpha=0.4)
ax.axhline(-Vc_phys, color='#C0392B', ls=':', lw=1, alpha=0.4)
ax.text(7, -Vc_phys * 0.5, 'ESCRITURA\n(→ bit "0")', ha='center',
        fontsize=10, color='#1A5276', fontweight='bold')
ax.text(t_wr * 0.5 + t_wait * 0.5, 0.2, 'ESPERA\n(0V, datos retenidos)',
        ha='center', fontsize=9, color='gray')
t_rd_center = (t_wr + t_wait + t_rd / 2) * 0.5
ax.text(t_rd_center, Vc_phys * 0.5, 'LECTURA', ha='center',
        fontsize=10, color='#E8963E', fontweight='bold')

# Panel 2: Polarización
ax = axes[1]
ax.plot(t_ns, p2_1 / p0 * Pr_phys, color='#E8963E', lw=2.5,
        label='Inicio: bit "1" (+Pr)')
ax.plot(t_ns, p2_0 / p0 * Pr_phys, color='#1A5276', lw=2.5, ls='--',
        label='Inicio: bit "0" (−Pr)')
ax.set_ylabel('P (µC/cm²)')
ax.axhline(0, color='gray', lw=0.3)
ax.axhline(Pr_phys, color='#E8963E', ls=':', lw=0.8, alpha=0.3)
ax.axhline(-Pr_phys, color='#1A5276', ls=':', lw=0.8, alpha=0.3)
ax.legend()
ax.annotate('Ambos → −Pr\n(escritura exitosa)', xy=(12, -Pr_phys * 0.7),
            fontsize=9, fontstyle='italic', ha='center')
ax.annotate('Datos retenidos\nsin alimentación',
            xy=(t_wr * 0.5 + t_wait * 0.35, -Pr_phys * 0.5),
            fontsize=9, color='gray', fontstyle='italic', ha='center')

# Panel 3: Corriente
ax = axes[2]
ax.plot(t_ns, i2_1, color='#E8963E', lw=2, label='Desde bit "1"')
ax.plot(t_ns, i2_0, color='#1A5276', lw=2, ls='--', label='Desde bit "0"')
ax.set_ylabel('Corriente (u.a.)')
ax.set_xlabel('Tiempo (ns)')
ax.axhline(0, color='gray', lw=0.3)
ax.legend()

# Anotar pico de lectura
rd_start = (t_wr + t_wait) * 0.5
rd_end = (t_wr + t_wait + t_rd) * 0.5
rd_mask = (t_ns > rd_start) & (t_ns < rd_end)
if np.any(rd_mask & (i2_0 > 0.5)):
    idx = np.where(rd_mask & (i2_0 > 0.5))[0]
    if len(idx) > 0:
        pk = idx[np.argmax(i2_0[idx])]
        ax.annotate('Pico grande = bit conmuta\n→ detectado como "0"',
                    xy=(t_ns[pk], i2_0[pk]),
                    xytext=(t_ns[pk] + 5, i2_0[pk] * 0.6),
                    fontsize=9, color='#1A5276', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='#1A5276', lw=1.5))

fig2.tight_layout()
fig2.savefig("../figures/fram_operation.png", dpi=150, bbox_inches="tight")
print("  ✓ Figura 2 lista")


# =====================================================================
# FIGURA 3: Transición de fase Pr(T)
# =====================================================================
print("[3/3] Calculando transición de fase Pr(T)...")

fig3, ax = plt.subplots(figsize=(7, 5))

T_range = np.linspace(100, 600, 500)
P_T = np.where(T_range < Tc,
               Pr_phys * np.sqrt(np.clip((Tc - T_range) / (Tc - 100), 0, None)),
               0)

ax.plot(T_range, P_T, color='#E8963E', lw=3, label='+Pr(T)')
ax.plot(T_range, -P_T, color='#1A5276', lw=3, label='−Pr(T)')
ax.axvline(Tc, color='#C0392B', ls='--', lw=1.5, alpha=0.7)
ax.text(Tc + 8, Pr_phys * 0.75, f'Tc = {Tc} K', fontsize=12,
        color='#C0392B', fontweight='bold')
ax.fill_betweenx([-25, 25], 100, Tc, alpha=0.05, color='#E8963E')
ax.fill_betweenx([-25, 25], Tc, 600, alpha=0.05, color='gray')
ax.text(280, 22, 'Ferroeléctrico\n(memoria funciona)', ha='center',
        fontsize=11, color='#E8963E', fontweight='bold')
ax.text(520, 22, 'Paraeléctrico\n(sin memoria)', ha='center',
        fontsize=11, color='gray', fontweight='bold')
ax.set_xlabel('Temperatura (K)')
ax.set_ylabel('Polarización remanente Pr (µC/cm²)')
ax.set_ylim(-25, 27)
ax.set_title('Transición de fase ferroeléctrica: Pr(T)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.15)
ax.legend()

fig3.tight_layout()
fig3.savefig("../figures/phase_transition.png", dpi=150, bbox_inches="tight")
print("  ✓ Figura 3 lista")

# =====================================================================
# Mostrar todo
# =====================================================================
print("\n" + "=" * 60)
print(" Mostrando 3 figuras. Cierra las ventanas para terminar.")
print("=" * 60)
# plt.show()  # disabled for headless execution