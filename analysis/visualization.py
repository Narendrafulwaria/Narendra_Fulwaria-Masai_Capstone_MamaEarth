# TASK 11: Save both PNGs to visualizations/ (uses the outlier-corrected series for the trend line)
import os
import matplotlib.pyplot as plt

# Create the output folder if it does not exist (fixes FileNotFoundError)
os.makedirs("visualizations", exist_ok=True)

# ---- Chart 1: return rate by payment method (descending, % labeled on each bar) ----
rate_by_pay = (merged.groupby("payment_method")["returned"].mean() * 100).round(1).sort_values(ascending=False)
ratio = rate_by_pay["COD"] / rate_by_pay["CARD"]

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(rate_by_pay.index, rate_by_pay.values,
              color=["#d62728" if m == "COD" else "#7f7f7f" for m in rate_by_pay.index])
for bar, val in zip(bars, rate_by_pay.values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.8, f"{val:.1f}%", ha="center", fontweight="bold")
ax.set_title(f"COD Returns at {rate_by_pay['COD']:.1f}% — {ratio:.0f}x Card")
ax.set_xlabel("Payment Method")
ax.set_ylabel("Return Rate (%)")
ax.set_ylim(0, rate_by_pay.max() + 8)
plt.tight_layout()
plt.savefig("visualizations/return_rate_by_payment.png", dpi=150)
plt.show()

# ---- Chart 2: outlier-corrected monthly revenue trend ----
peak_month = monthly_corrected.idxmax()
peak_value = monthly_corrected.max()

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(monthly_corrected.index, monthly_corrected.values, marker="o", linewidth=2, color="#1f77b4")
ax.scatter([peak_month], [peak_value], color="#d62728", zorder=5, s=90)
ax.annotate(f"Peak: INR {peak_value:,.0f}", (peak_month, peak_value),
            textcoords="offset points", xytext=(0, 10), ha="center")
ax.set_title(f"Outlier-Corrected Monthly Revenue — Peak in {peak_month}")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (INR)")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("visualizations/monthly_revenue_trend.png", dpi=150)
plt.show()

# print(os.listdir("visualizations"))

