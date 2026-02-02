import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
import pandas as pd
import numpy as np
from functools import partial

from optimizer import optimize_portfolio_cvar_milp, SolveConfig, SectorBounds


def load_prices_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=True, index_col=0)
    # Expect columns = tickers, rows = dates, values = close prices
    return df.sort_index()


def compute_returns_and_mu(prices: pd.DataFrame) -> (pd.DataFrame, pd.Series):
    returns = prices.pct_change().dropna(how="all")
    mu = returns.mean() * 252
    return returns, mu


class DesktopGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Portfolio Optimizer — Desktop")
        root.geometry("820x640")

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # Inputs frame
        left = ttk.Frame(frm)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        ttk.Label(left, text="Tickers (comma-separated):").pack(anchor=tk.W)
        self.tickers_var = tk.StringVar(value="AAPL,MSFT,AMZN")
        ttk.Entry(left, textvariable=self.tickers_var, width=30).pack(anchor=tk.W, pady=4)

        ttk.Label(left, text="Local prices CSV:").pack(anchor=tk.W, pady=(8, 0))
        self.prices_path_var = tk.StringVar()
        pframe = ttk.Frame(left)
        pframe.pack(anchor=tk.W, pady=4)
        ttk.Entry(pframe, textvariable=self.prices_path_var, width=28).pack(side=tk.LEFT)
        ttk.Button(pframe, text="Browse", command=self.browse_prices).pack(side=tk.LEFT, padx=6)

        ttk.Label(left, text="Optional: sectors CSV (ticker,sector,region):").pack(anchor=tk.W, pady=(8, 0))
        self.sectors_path_var = tk.StringVar()
        sframe = ttk.Frame(left)
        sframe.pack(anchor=tk.W, pady=4)
        ttk.Entry(sframe, textvariable=self.sectors_path_var, width=28).pack(side=tk.LEFT)
        ttk.Button(sframe, text="Browse", command=self.browse_sectors).pack(side=tk.LEFT, padx=6)

        ttk.Label(left, text="Optional: current weights CSV (ticker,weight):").pack(anchor=tk.W, pady=(8, 0))
        self.w0_path_var = tk.StringVar()
        wframe = ttk.Frame(left)
        wframe.pack(anchor=tk.W, pady=4)
        ttk.Entry(wframe, textvariable=self.w0_path_var, width=28).pack(side=tk.LEFT)
        ttk.Button(wframe, text="Browse", command=self.browse_w0).pack(side=tk.LEFT, padx=6)

        # Params
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        self.beta_var = tk.DoubleVar(value=0.95)
        ttk.Label(left, text="CVaR beta:").pack(anchor=tk.W)
        ttk.Entry(left, textvariable=self.beta_var, width=10).pack(anchor=tk.W, pady=2)

        self.lambda_var = tk.DoubleVar(value=5.0)
        ttk.Label(left, text="Lambda (risk aversion):").pack(anchor=tk.W)
        ttk.Entry(left, textvariable=self.lambda_var, width=10).pack(anchor=tk.W, pady=2)

        self.nmax_var = tk.IntVar(value=10)
        ttk.Label(left, text="Max assets (cardinality):").pack(anchor=tk.W)
        ttk.Entry(left, textvariable=self.nmax_var, width=10).pack(anchor=tk.W, pady=2)

        self.wmax_var = tk.DoubleVar(value=0.5)
        ttk.Label(left, text="Max weight per asset:").pack(anchor=tk.W)
        ttk.Entry(left, textvariable=self.wmax_var, width=10).pack(anchor=tk.W, pady=2)

        self.turn_var = tk.DoubleVar(value=0.30)
        ttk.Label(left, text="Max turnover (L1):").pack(anchor=tk.W)
        ttk.Entry(left, textvariable=self.turn_var, width=10).pack(anchor=tk.W, pady=2)

        self.tc_rate_var = tk.DoubleVar(value=0.001)
        ttk.Label(left, text="Transaction cost rate:").pack(anchor=tk.W)
        ttk.Entry(left, textvariable=self.tc_rate_var, width=10).pack(anchor=tk.W, pady=2)

        self.tc_fixed_var = tk.DoubleVar(value=0.0)
        ttk.Label(left, text="Fixed trade cost:").pack(anchor=tk.W)
        ttk.Entry(left, textvariable=self.tc_fixed_var, width=10).pack(anchor=tk.W, pady=2)

        ttk.Label(left, text="Solver:").pack(anchor=tk.W, pady=(8, 0))
        self.solver_var = tk.StringVar(value="CBC")
        ttk.Combobox(left, textvariable=self.solver_var, values=["CBC", "SCIP"], width=8).pack(anchor=tk.W)

        ttk.Button(left, text="Run Optimization (local only)", command=self.run_optimization).pack(pady=12, fill=tk.X)

        # Right: results
        right = ttk.Frame(frm)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(right, text="Results:").pack(anchor=tk.W)
        self.txt = tk.Text(right, wrap=tk.NONE)
        self.txt.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(right)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Save Weights CSV", command=self.save_weights).pack(side=tk.LEFT, padx=6, pady=6)

        self.last_df = None

    def browse_prices(self):
        p = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv" )])
        if p:
            self.prices_path_var.set(p)

    def browse_sectors(self):
        p = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv" )])
        if p:
            self.sectors_path_var.set(p)

    def browse_w0(self):
        p = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv" )])
        if p:
            self.w0_path_var.set(p)

    def run_optimization(self):
        prices_path = self.prices_path_var.get().strip()
        if not prices_path:
            messagebox.showerror("Data required", "Please select a local prices CSV file (no internet).")
            return
        try:
            prices = load_prices_csv(prices_path)
        except Exception as e:
            messagebox.showerror("Error reading CSV", str(e))
            return

        tickers = [t.strip().upper() for t in self.tickers_var.get().split(",") if t.strip()]
        missing = [t for t in tickers if t not in prices.columns]
        if missing:
            messagebox.showerror("Tickers missing", f"The following tickers are not columns in the prices CSV: {missing}")
            return

        returns, mu = compute_returns_and_mu(prices[tickers])

        sector_map = None
        sectors_path = self.sectors_path_var.get().strip()
        if sectors_path:
            try:
                sdf = pd.read_csv(sectors_path)
                sector_map = {row[0]: row[1] for row in sdf.values}
            except Exception as e:
                messagebox.showwarning("Sectors CSV", f"Could not load sectors CSV: {e}")

        w0 = None
        w0_path = self.w0_path_var.get().strip()
        if w0_path:
            try:
                wdf = pd.read_csv(w0_path)
                w0 = {str(r[0]).upper(): float(r[1]) for r in wdf.values}
            except Exception as e:
                messagebox.showwarning("Weights CSV", f"Could not load weights CSV: {e}")

        cfg = SolveConfig(
            beta=float(self.beta_var.get()),
            lambda_cvar=float(self.lambda_var.get()),
            n_max_assets=int(self.nmax_var.get()),
            min_weight_if_selected=0.0,
            max_weight_per_asset=float(self.wmax_var.get()),
            turnover_max=float(self.turn_var.get()),
            tc_rate=float(self.tc_rate_var.get()),
            tc_fixed=float(self.tc_fixed_var.get()),
            solver_preference=self.solver_var.get(),
            time_limit_sec=30,
        )

        try:
            res = optimize_portfolio_cvar_milp(
                tickers=tickers,
                scenario_returns=returns,
                mu=mu,
                w0=w0,
                sector_map=sector_map,
                sector_bounds=None,
                config=cfg,
            )
        except Exception as e:
            messagebox.showerror("Optimization error", str(e))
            return

        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, f"Status: {res.status}\n\n")
        if not res.weights:
            self.txt.insert(tk.END, "No solution.\n")
            return

        df = pd.DataFrame({
            "ticker": tickers,
            "weight": [res.weights.get(t, 0.0) for t in tickers],
            "selected": [res.selected.get(t, 0) for t in tickers],
        })
        df = df[df["weight"] > 1e-8].sort_values("weight", ascending=False).reset_index(drop=True)
        self.last_df = df

        self.txt.insert(tk.END, df.to_string(index=False))
        self.txt.insert(tk.END, "\n\nMetrics:\n")
        self.txt.insert(tk.END, f"Expected return (annual): {res.exp_return:.6f}\n")
        self.txt.insert(tk.END, f"CVaR: {res.cvar:.6f}\n")
        self.txt.insert(tk.END, f"Turnover: {res.turnover:.6f}\n")
        self.txt.insert(tk.END, f"Objective: {res.objective:.6f}\n")

    def save_weights(self):
        if self.last_df is None:
            messagebox.showinfo("No data", "No weights to save. Run optimization first.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not p:
            return
        self.last_df.to_csv(p, index=False)
        messagebox.showinfo("Saved", f"Saved weights to {p}")


def main():
    root = tk.Tk()
    app = DesktopGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
