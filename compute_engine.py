import numpy as np
from scipy.optimize import least_squares,fsolve
import math
from sympy import symbols, Eq, solve

def compute_engine(F, Z, T, q, xD2, antoine_constants):
    T=T+273.5 #kelvin
    antoine_constants = np.array(antoine_constants)
    def solve_mass_balance(F, xF, xD2):
      xF1, xF2, xF3, xF4 = xF
      def equations(vars):
        D, B, xD1, xD3, a, b = vars

        # Reparametrize xB
        xB2 = a
        xB3 = b
        xB4 = 1 - a - b  # ensures xB sums to 1
        xB = [0, xB2, xB3, xB4]

        # Equations
        eq1 = D + B - F
        eq2 = xD1 * D - xF1 * F
        eq3 = xD2 * D + xB2 * B - xF2 * F
        eq4 = xD3 * D + xB3 * B - xF3 * F
        eq5 = xB4 * B - xF4 * F
        eq6 = xD1 + xD2 + xD3 - 1  # ensures xD sums to 1

        return [eq1, eq2, eq3, eq4, eq5, eq6]
    
      # Initial guess: [D, B, xD1, xD3, a, b]
      guess = [0.5 * F, 0.5 * F, 0.3, 0.3, 0.3, 0.3]

      # Bounds for: [D, B, xD1, xD3, a, b]
      lower_bounds = [0, 0, 0, 0, 0, 0]
      upper_bounds = [F, F, 1, 1, 1, 1]

      result = least_squares(
          equations,
          guess,
          bounds=(lower_bounds, upper_bounds)
      )

      if not result.success:
          raise RuntimeError(f"Solver failed: {result.message}")

      D, B, xD1, xD3, a, b = result.x
      xD = [xD1, xD2, xD3, 0]
      xB = [0, a, b, 1 - a - b]

      return {
          "D": D,
          "B": B,
          "xD": xD,
          "xB": xB
      }

    xF = Z  # Feed composition
    result = solve_mass_balance(F, xF, xD2)

    D = result["D"]
    B = result["B"]
    xD = result["xD"]
    xB = result["xB"]
    xD1, xD2, xD3, xD4=xD
    xB1, xB2, xB3, xB4=xB

    print(f"Distillate flow rate (D): {D:.2f}")
    print(f"Bottom flow rate (B): {B:.2f}")
    print(f"Distillate composition (xD): {xD}")
    print(f"Bottom composition (xB): {xB}")

    # Relative volatility
    def find_alpha(antoine_constants, T):
        psat = []
        alpha = []
        hk = 10**(antoine_constants[2, 0] - (antoine_constants[2, 1] / (T + antoine_constants[2, 2])))
        for i in range(4):
            p = 10**(antoine_constants[i, 0] - (antoine_constants[i, 1] / (T + antoine_constants[i, 2])))
            psat.append(p)
            alpha.append(p / hk)
        return alpha

    alpha = find_alpha(antoine_constants, T)
    print(f"The relative volatility is: {alpha}")

    # Fenske minimum stages
    def fenske_min_stages(xD, xB, alpha):
        if not (0 < xD < 1 and 0 < xB < 1):
            raise ValueError("xD and xB must be between 0 and 1")
        term1 = xD / (1 - xD)
        term2 = xB / (1 - xB)
        N_min = math.log(term1 / term2) / math.log(alpha[1])
        return N_min

    N_min = fenske_min_stages(xD2, xB3, alpha)
    print(f"Minimum number of stages (Nmin) from Fenske: {N_min:.2f}")

    # Underwood method
    def underwood_theta(alpha, z, q):
        def underwood_eq(theta):
            return sum([q * zi / (ai - theta) for zi, ai in zip(z, alpha)]) - 1
        theta_guess = min(alpha) - 0.01
        theta_solution = fsolve(underwood_eq, theta_guess)
        return theta_solution[0]

    def underwood_min_reflux_ratio(alpha, xD, z, q):
        theta = underwood_theta(alpha, z, q)
        Rmin = sum([ai * xdi / (ai - theta) for ai, xdi in zip(alpha, xD)]) - 1
        return Rmin, theta

    Rmin, theta = underwood_min_reflux_ratio(alpha, xD, Z, q)
    print(f"Underwood theta: {theta:.4f}")
    print(f"Minimum reflux ratio (Rmin): {Rmin:.4f}")

    return {
    "Distillate Flow Rate": round(D, 2),
    "Bottom Flow Rate": round(B, 2),
    "Distillate Composition": [round(x, 2) for x in [xD1, xD2, xD3, xD4]],
    "Bottom Composition": [round(x, 2) for x in [xB1, xB2, xB3, xB4]],
    "Minimum Theoretical Stages (Fenske)": round(N_min, 2),
    "Minimum Reflux Ratio (Underwood)": round(Rmin, 2),
    "Underwood Theta": round(theta, 2),
    "Temperature": T,  # or whatever processed temperature you're using
    "Gasoline %": xD2 * 100,
    "Kerosene %":  xB3* 100
}

