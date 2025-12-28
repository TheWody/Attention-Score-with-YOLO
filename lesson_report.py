from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import webbrowser
import tempfile

try:
    from scipy import stats
    SCIPY_OK = True
except Exception:
    SCIPY_OK = False

def _format_pvalue(p: float) -> str:
    if np.isnan(p):
        return "NA"
    if p < 0.001:
        return "< 0.001"
    return f"{p:.3f}"

def compute_kpis_and_test(
    minutes: np.ndarray,
    att_pct: np.ndarray,
    attentive_counts: np.ndarray,
    distracted_counts: np.ndarray,
    hypothesized_mean: float = 60.0,
    alpha: float = 0.05
) -> dict:
    n_minutes = len(minutes)

    subgroup_n = attentive_counts + distracted_counts
    subgroup_n = np.where(subgroup_n <= 0, np.nan, subgroup_n)
    p_dis = distracted_counts / subgroup_n

    if n_minutes > 1:
        slope = float(np.polyfit(minutes.astype(float), att_pct.astype(float), 1)[0])
    else:
        slope = 0.0

    mean = float(np.nanmean(att_pct))
    sd = float(np.nanstd(att_pct, ddof=1)) if n_minutes > 1 else 0.0
    se = sd / np.sqrt(n_minutes) if n_minutes > 0 and sd > 0 else float("nan")

    dfree = n_minutes - 1
    t_stat = (mean - hypothesized_mean) / se if (se and se > 0 and not np.isnan(se)) else float("nan")

    if SCIPY_OK and not np.isnan(t_stat) and dfree > 0:
        p_value = float(stats.t.sf(t_stat, df=dfree))
        tcrit_2s = float(stats.t.ppf(1 - alpha / 2, df=dfree))
        tcrit_1s = float(stats.t.ppf(1 - alpha, df=dfree))
    else:
        from math import erf, sqrt
        p_value = float(0.5 * (1 - erf(t_stat / sqrt(2)))) if not np.isnan(t_stat) else float("nan")
        tcrit_2s = 2.02
        tcrit_1s = 1.68

    ci_low = mean - tcrit_2s * se if not np.isnan(se) else mean
    ci_high = mean + tcrit_2s * se if not np.isnan(se) else mean
    lower_bound_95 = mean - tcrit_1s * se if not np.isnan(se) else mean

    reject = (p_value < alpha) if not np.isnan(p_value) else False
    if reject:
        user_statement = f"Average attention score is greater than {hypothesized_mean:.0f}%."
    else:
        user_statement = f"Average attention score is NOT greater than {hypothesized_mean:.0f}% (insufficient evidence)."

    return {
        "n_minutes": n_minutes,
        "mean_attention_pct": mean,
        "sd_attention_pct": sd,
        "se_attention_pct": float(se) if not np.isnan(se) else 0.0,
        "median_attention_pct": float(np.nanmedian(att_pct)) if n_minutes > 0 else 0.0,
        "min_attention_pct": float(np.nanmin(att_pct)) if n_minutes > 0 else 0.0,
        "max_attention_pct": float(np.nanmax(att_pct)) if n_minutes > 0 else 0.0,
        "mean_distracted_p": float(np.nanmean(p_dis)) if n_minutes > 0 else 0.0,
        "min_distracted_p": float(np.nanmin(p_dis)) if n_minutes > 0 else 0.0,
        "max_distracted_p": float(np.nanmax(p_dis)) if n_minutes > 0 else 0.0,
        "minutes_above_60pct": int(np.sum(att_pct >= 60)),
        "minutes_below_60pct": int(np.sum(att_pct < 60)),
        "trend_slope_pct_per_min": slope,
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "lower_bound_95": float(lower_bound_95),
        "t_stat": float(t_stat) if not np.isnan(t_stat) else 0.0,
        "dfree": int(dfree),
        "p_value": float(p_value) if not np.isnan(p_value) else 1.0,
        "p_text": _format_pvalue(float(p_value)) if not np.isnan(p_value) else "NA",
        "reject": bool(reject),
        "user_statement": user_statement,
        "hypothesized_mean": float(hypothesized_mean),
        "alpha": float(alpha),
        "minutes_series": minutes,
        "att_pct_series": att_pct,
        "p_dis_series": p_dis,
    }

def make_plots(k: dict, title: str, assets_dir: Path) -> tuple:
    assets_dir.mkdir(parents=True, exist_ok=True)

    minutes = k["minutes_series"]
    att_pct = k["att_pct_series"]
    p_dis = k["p_dis_series"]

    plt.figure(figsize=(10, 5))
    plt.plot(minutes, att_pct, marker="o", linewidth=2, markersize=6, color="#005bbb")
    plt.axhline(y=60, color='red', linestyle='--', alpha=0.7, label='60% threshold')
    plt.fill_between(minutes, att_pct, alpha=0.3, color="#005bbb")
    plt.xlabel("Minute", fontsize=12)
    plt.ylabel("Attention (%)", fontsize=12)
    plt.title(f"{title} - Attention Score Over Time", fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    p1 = assets_dir / "attention_vs_minute.png"
    plt.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(minutes, p_dis * 100, marker="o", linewidth=2, markersize=6, color="#e84545")
    plt.fill_between(minutes, p_dis * 100, alpha=0.3, color="#e84545")
    plt.xlabel("Minute", fontsize=12)
    plt.ylabel("Distracted Students (%)", fontsize=12)
    plt.title(f"{title} - Distracted Proportion Over Time", fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    p2 = assets_dir / "distracted_proportion_vs_minute.png"
    plt.savefig(p2, dpi=150, bbox_inches="tight")
    plt.close()

    return p1.name, p2.name

def build_html(title: str, k: dict, course_info: dict, teacher_name: str,
               duration_str: str, assets_dir_name: str, img1: str, img2: str) -> str:
    trend_text = "decreasing ↓" if k["trend_slope_pct_per_min"] < 0 else "increasing ↑"
    trend_color = "#e84545" if k["trend_slope_pct_per_min"] < 0 else "#29b566"
    decision = "✓ Reject H0" if k["reject"] else "✗ Fail to reject H0"
    decision_color = "#29b566" if k["reject"] else "#e84545"

    mean_score = k["mean_attention_pct"]
    if mean_score >= 70:
        score_color = "#29b566"
        score_label = "Good"
    elif mean_score >= 50:
        score_color = "#f0a500"
        score_label = "Average"
    else:
        score_color = "#e84545"
        score_label = "Needs Improvement"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{title} - Lesson Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 30px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .header h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 16px;
        }}
        .header .meta {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .header .meta-item {{
            background: #f5f5f5;
            padding: 10px 20px;
            border-radius: 8px;
        }}
        .header .meta-item strong {{
            color: #333;
        }}
        .score-hero {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .score-value {{
            font-size: 72px;
            font-weight: 700;
            color: {score_color};
        }}
        .score-label {{
            font-size: 24px;
            color: #666;
            margin-top: 10px;
        }}
        .score-badge {{
            display: inline-block;
            background: {score_color};
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            margin-top: 15px;
        }}
        .statement {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            font-size: 18px;
            color: #333;
            border-left: 4px solid {decision_color};
        }}
        .card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .card h2 {{
            color: #333;
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .kpi-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .kpi-item .value {{
            font-size: 24px;
            font-weight: 700;
            color: #333;
        }}
        .kpi-item .label {{
            font-size: 13px;
            color: #666;
            margin-top: 5px;
        }}
        .trend {{
            color: {trend_color};
            font-weight: 600;
        }}
        .chart-container {{
            margin-top: 20px;
        }}
        .chart-container img {{
            width: 100%;
            border-radius: 10px;
            border: 1px solid #eee;
            margin-bottom: 15px;
        }}
        .test-results {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}
        .test-item {{
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .test-item strong {{
            color: #333;
        }}
        .decision {{
            padding: 15px;
            background: {decision_color}15;
            border-radius: 10px;
            border-left: 4px solid {decision_color};
            margin-top: 15px;
        }}
        .decision strong {{
            color: {decision_color};
        }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <p class="subtitle">End-of-Lesson Attention Analysis Report</p>
            <div class="meta">
                <div class="meta-item"><strong>Teacher:</strong> {teacher_name}</div>
                <div class="meta-item"><strong>Course:</strong> {course_info.get('course_code', '')} - {course_info.get('course_name', '')}</div>
                <div class="meta-item"><strong>Duration:</strong> {duration_str}</div>
                <div class="meta-item"><strong>Location:</strong> {course_info.get('classroom_location', 'N/A')}</div>
            </div>
        </div>

        <div class="score-hero">
            <div class="score-value">{k["mean_attention_pct"]:.1f}%</div>
            <div class="score-label">Average Attention Score</div>
            <div class="score-badge">{score_label}</div>
            <div class="statement">{k["user_statement"]}</div>
        </div>

        <div class="card">
            <h2>📈 Key Metrics</h2>
            <div class="kpi-grid">
                <div class="kpi-item">
                    <div class="value">{k["n_minutes"]}</div>
                    <div class="label">Minutes Analyzed</div>
                </div>
                <div class="kpi-item">
                    <div class="value">{k["median_attention_pct"]:.1f}%</div>
                    <div class="label">Median Attention</div>
                </div>
                <div class="kpi-item">
                    <div class="value">{k["min_attention_pct"]:.1f}% - {k["max_attention_pct"]:.1f}%</div>
                    <div class="label">Min / Max Attention</div>
                </div>
                <div class="kpi-item">
                    <div class="value">{k["sd_attention_pct"]:.2f}</div>
                    <div class="label">Std. Deviation</div>
                </div>
                <div class="kpi-item">
                    <div class="value">{k["mean_distracted_p"]*100:.1f}%</div>
                    <div class="label">Avg. Distracted Rate</div>
                </div>
                <div class="kpi-item">
                    <div class="value">{k["minutes_above_60pct"]} / {k["n_minutes"]}</div>
                    <div class="label">Minutes Above 60%</div>
                </div>
                <div class="kpi-item">
                    <div class="value">({k["ci_low"]:.1f}%, {k["ci_high"]:.1f}%)</div>
                    <div class="label">95% Confidence Interval</div>
                </div>
                <div class="kpi-item">
                    <div class="value trend">{k["trend_slope_pct_per_min"]:.2f}%/min {trend_text}</div>
                    <div class="label">Attention Trend</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📉 Visualizations</h2>
            <div class="chart-container">
                <img src="{assets_dir_name}/{img1}" alt="Attention vs Time">
                <img src="{assets_dir_name}/{img2}" alt="Distracted Proportion vs Time">
            </div>
        </div>

        <div class="card">
            <h2>🧪 Statistical Analysis (One-Sample t-Test)</h2>
            <div class="test-results">
                <div class="test-item"><strong>Null Hypothesis (H₀):</strong> μ = {k["hypothesized_mean"]:.0f}%</div>
                <div class="test-item"><strong>Alternative (H₁):</strong> μ > {k["hypothesized_mean"]:.0f}%</div>
                <div class="test-item"><strong>Test Statistic:</strong> t = {k["t_stat"]:.3f}</div>
                <div class="test-item"><strong>Degrees of Freedom:</strong> df = {k["dfree"]}</div>
                <div class="test-item"><strong>P-Value:</strong> {k["p_text"]}</div>
                <div class="test-item"><strong>Significance Level:</strong> α = {k["alpha"]:.2f}</div>
            </div>
            <div class="decision">
                <strong>{decision}</strong> at α = {k["alpha"]:.2f}<br>
                <span style="color: #666; font-size: 14px;">
                    {k["user_statement"]}
                </span>
            </div>
        </div>

        <div class="footer">
            <p>Generated by Classroom Attention Monitor</p>
        </div>
    </div>
</body>
</html>"""
    return html

def generate_lesson_report(
    minute_data: list,
    course_info: dict,
    teacher_name: str,
    duration_seconds: int,
    avg_attention_score: float,
    hypothesized_mean: float = 60.0,
    alpha: float = 0.05,
    open_browser: bool = True
) -> Path:
    report_dir = Path(tempfile.gettempdir()) / "attention_reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    course_code = course_info.get('course_code', 'lesson').replace(' ', '_')
    report_folder = report_dir / f"{course_code}_{timestamp}"
    report_folder.mkdir(parents=True, exist_ok=True)
    assets_dir = report_folder / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    if minute_data and len(minute_data) > 0:
        minutes = np.array([d['minute_number'] for d in minute_data])
        att_pct = np.array([d['avg_score'] for d in minute_data])
        attentive = np.array([d['avg_attentive'] for d in minute_data])
        distracted = np.array([d['avg_distracted'] for d in minute_data])
    else:
        minutes = np.array([1])
        att_pct = np.array([avg_attention_score])
        attentive = np.array([1])
        distracted = np.array([0])

    k = compute_kpis_and_test(
        minutes=minutes,
        att_pct=att_pct,
        attentive_counts=attentive,
        distracted_counts=distracted,
        hypothesized_mean=hypothesized_mean,
        alpha=alpha
    )

    title = f"{course_info.get('course_code', '')} - {course_info.get('course_name', 'Lesson')}"
    img1, img2 = make_plots(k, title, assets_dir)

    mins = duration_seconds // 60
    secs = duration_seconds % 60
    duration_str = f"{mins} min {secs} sec"

    html = build_html(
        title=title,
        k=k,
        course_info=course_info,
        teacher_name=teacher_name,
        duration_str=duration_str,
        assets_dir_name=assets_dir.name,
        img1=img1,
        img2=img2
    )

    html_path = report_folder / "lesson_report.html"
    html_path.write_text(html, encoding="utf-8")

    print(f"Report saved: {html_path}")

    if open_browser:
        webbrowser.open(f"file://{html_path}")

    return html_path
