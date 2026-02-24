#!/usr/bin/env python3
"""
Business Analytics Chart Generation Script
Generates visualizations focused on business insights and decision-making
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style for professional business charts
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 11

# Create charts directory
CHARTS_DIR = Path('charts')
CHARTS_DIR.mkdir(exist_ok=True)

# Load data
print("Loading data...")
df = pd.read_csv('data/taxpayers_all_regions.csv')
summary_df = pd.read_csv('data/taxpayers_all_regions_summary.csv')

print(f"Loaded {len(df)} company records from {df['region'].nunique()} regions")


def chart_1_company_status_overview():
    """Business Health: Company Status Distribution"""
    print("Generating Chart 1: Company Status Overview...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Active vs Inactive
    status_counts = df['taxpayerStatus_name_az'].value_counts()
    colors = ['#2ecc71', '#e74c3c']
    ax1.bar(range(len(status_counts)), status_counts.values, color=colors, alpha=0.8)
    ax1.set_xticks(range(len(status_counts)))
    ax1.set_xticklabels(['Active', 'Stopped'], fontsize=12)
    ax1.set_ylabel('Number of Companies', fontsize=12)
    ax1.set_title('Company Operational Status', fontsize=14, fontweight='bold')

    # Add value labels
    for i, v in enumerate(status_counts.values):
        percentage = (v / len(df)) * 100
        ax1.text(i, v + 50, f'{v:,}\n({percentage:.1f}%)', ha='center', fontsize=11, fontweight='bold')

    ax1.set_ylim(0, max(status_counts.values) * 1.15)

    # Active companies breakdown
    active_metrics = pd.DataFrame({
        'Metric': ['Total Active', 'VAT Registered', 'With Debt', 'Risky Status'],
        'Count': [
            df['active'].sum(),
            df['vatPayer'].sum(),
            (df['debt'] > 0).sum(),
            df['riskyPayer'].sum()
        ]
    })

    colors2 = ['#3498db', '#f39c12', '#e67e22', '#c0392b']
    bars = ax2.barh(active_metrics['Metric'], active_metrics['Count'], color=colors2, alpha=0.8)
    ax2.set_xlabel('Number of Companies', fontsize=12)
    ax2.set_title('Active Company Profile', fontsize=14, fontweight='bold')

    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        percentage = (width / len(df)) * 100
        ax2.text(width + 50, bar.get_y() + bar.get_height()/2,
                f'{int(width):,} ({percentage:.1f}%)',
                va='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '01_company_status_overview.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 01_company_status_overview.png")


def chart_2_regional_debt_concentration():
    """Financial Risk: Regional Debt Distribution"""
    print("Generating Chart 2: Regional Debt Concentration...")

    regional_debt = df.groupby('region').agg({
        'debt': 'sum',
        'tin': 'count'
    }).reset_index()
    regional_debt.columns = ['region', 'total_debt', 'company_count']
    regional_debt = regional_debt.sort_values('total_debt', ascending=False).head(15)

    fig, ax = plt.subplots(figsize=(14, 7))

    # Convert to millions for readability
    regional_debt['debt_millions'] = regional_debt['total_debt'] / 1_000_000

    colors = ['#c0392b' if debt > 5 else '#e74c3c' if debt > 2 else '#f39c12'
              for debt in regional_debt['debt_millions']]

    bars = ax.barh(range(len(regional_debt)), regional_debt['debt_millions'], color=colors, alpha=0.8)
    ax.set_yticks(range(len(regional_debt)))
    ax.set_yticklabels(regional_debt['region'], fontsize=11)
    ax.set_xlabel('Total Debt (Million AZN)', fontsize=12)
    ax.set_title('Top 15 Regions by Total Company Debt - Financial Risk Exposure',
                 fontsize=14, fontweight='bold')

    # Add value labels
    for i, (idx, row) in enumerate(regional_debt.iterrows()):
        ax.text(row['debt_millions'] + 0.15, i,
               f"{row['debt_millions']:.2f}M AZN",
               va='center', fontsize=10, fontweight='bold')

    ax.set_xlim(0, max(regional_debt['debt_millions']) * 1.15)
    ax.invert_yaxis()

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#c0392b', alpha=0.8, label='High Risk (>5M AZN)'),
        Patch(facecolor='#e74c3c', alpha=0.8, label='Medium Risk (2-5M AZN)'),
        Patch(facecolor='#f39c12', alpha=0.8, label='Lower Risk (<2M AZN)')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '02_regional_debt_concentration.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 02_regional_debt_concentration.png")


def chart_3_organization_type_distribution():
    """Market Structure: Organization Type Mix"""
    print("Generating Chart 3: Organization Type Distribution...")

    org_types = df['organizationType'].value_counts().head(8)

    fig, ax = plt.subplots(figsize=(12, 7))

    colors = sns.color_palette("Set2", len(org_types))
    bars = ax.bar(range(len(org_types)), org_types.values, color=colors, alpha=0.85)

    ax.set_xticks(range(len(org_types)))
    ax.set_xticklabels([
        'Limited\nLiability\nCompany',
        'Other\nCommercial\nOrg',
        'Public\nAssociation',
        'Other\nNon-Profit',
        'Cooperative',
        'Open Joint\nStock Co',
        'Full\nPartnership',
        'State\nManagement'
    ], fontsize=10)

    ax.set_ylabel('Number of Companies', fontsize=12)
    ax.set_title('Market Composition by Organization Type', fontsize=14, fontweight='bold')

    # Add value labels and percentages
    for i, v in enumerate(org_types.values):
        percentage = (v / len(df)) * 100
        ax.text(i, v + 30, f'{v:,}\n({percentage:.1f}%)',
               ha='center', fontsize=10, fontweight='bold')

    ax.set_ylim(0, max(org_types.values) * 1.15)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '03_organization_type_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 03_organization_type_distribution.png")


def chart_4_vat_compliance_by_org_type():
    """Tax Compliance: VAT Registration Rates"""
    print("Generating Chart 4: VAT Compliance by Organization Type...")

    org_vat = df.groupby('organizationType').agg({
        'tin': 'count',
        'vatPayer': 'sum'
    }).reset_index()
    org_vat.columns = ['org_type', 'total', 'vat_payers']
    org_vat['vat_rate'] = (org_vat['vat_payers'] / org_vat['total'] * 100).round(1)
    org_vat = org_vat.sort_values('total', ascending=False).head(8)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(org_vat))
    width = 0.35

    colors1 = '#3498db'
    colors2 = '#2ecc71'

    bars1 = ax.bar(x - width/2, org_vat['total'], width, label='Total Companies',
                   color=colors1, alpha=0.8)
    bars2 = ax.bar(x + width/2, org_vat['vat_payers'], width, label='VAT Registered',
                   color=colors2, alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels([
        'LLC', 'Other\nCommercial', 'Public\nAssociation',
        'Other\nNon-Profit', 'Cooperative', 'Open\nJSC',
        'State\nManagement', 'Fund'
    ], fontsize=10)

    ax.set_ylabel('Number of Companies', fontsize=12)
    ax.set_title('VAT Registration Compliance by Organization Type', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)

    # Add VAT rate labels
    for i, (idx, row) in enumerate(org_vat.iterrows()):
        ax.text(i, row['total'] + 50, f'{row["vat_rate"]:.1f}%',
               ha='center', fontsize=9, fontweight='bold', color='#c0392b')

    ax.set_ylim(0, max(org_vat['total']) * 1.15)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '04_vat_compliance_by_org_type.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 04_vat_compliance_by_org_type.png")


def chart_5_company_registration_trends():
    """Growth Trends: Company Registration Over Time"""
    print("Generating Chart 5: Company Registration Trends...")

    df['reg_year'] = pd.to_datetime(df['voenRegisteredAt'], errors='coerce').dt.year
    df_recent = df[df['reg_year'] >= 2010]

    yearly_registrations = df_recent.groupby('reg_year').size().reset_index()
    yearly_registrations.columns = ['year', 'registrations']

    fig, ax = plt.subplots(figsize=(14, 6))

    colors = ['#e74c3c' if count < 30 else '#f39c12' if count < 45 else '#2ecc71'
              for count in yearly_registrations['registrations']]

    bars = ax.bar(yearly_registrations['year'], yearly_registrations['registrations'],
                  color=colors, alpha=0.8, width=0.7)

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Number of New Registrations', fontsize=12)
    ax.set_title('Annual Company Registration Trend (2010-2026)',
                 fontsize=14, fontweight='bold')

    # Add value labels
    for i, (idx, row) in enumerate(yearly_registrations.iterrows()):
        ax.text(row['year'], row['registrations'] + 1.5, f"{int(row['registrations'])}",
               ha='center', fontsize=9, fontweight='bold')

    ax.set_ylim(0, max(yearly_registrations['registrations']) * 1.15)
    ax.set_xticks(yearly_registrations['year'])
    ax.set_xticklabels(yearly_registrations['year'].astype(int), rotation=45)

    # Add trend line
    z = np.polyfit(yearly_registrations['year'], yearly_registrations['registrations'], 2)
    p = np.poly1d(z)
    ax.plot(yearly_registrations['year'], p(yearly_registrations['year']),
           "k--", alpha=0.5, linewidth=2, label='Trend')
    ax.legend(fontsize=10)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '05_company_registration_trends.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 05_company_registration_trends.png")


def chart_6_debt_distribution_analysis():
    """Financial Health: Debt Distribution Pattern"""
    print("Generating Chart 6: Debt Distribution Analysis...")

    companies_with_debt = df[df['debt'] > 0].copy()
    companies_without_debt = len(df) - len(companies_with_debt)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Chart 1: Debt vs No Debt
    categories = ['No Debt', 'With Debt']
    values = [companies_without_debt, len(companies_with_debt)]
    colors = ['#2ecc71', '#e74c3c']

    bars = ax1.bar(categories, values, color=colors, alpha=0.8, width=0.5)
    ax1.set_ylabel('Number of Companies', fontsize=12)
    ax1.set_title('Company Debt Status Distribution', fontsize=14, fontweight='bold')

    for i, v in enumerate(values):
        percentage = (v / len(df)) * 100
        ax1.text(i, v + 50, f'{v:,}\n({percentage:.1f}%)',
                ha='center', fontsize=11, fontweight='bold')

    ax1.set_ylim(0, max(values) * 1.15)

    # Chart 2: Debt Range Distribution
    debt_ranges = [
        (0, 100, 'Under 100 AZN'),
        (100, 1000, '100-1K AZN'),
        (1000, 10000, '1K-10K AZN'),
        (10000, 100000, '10K-100K AZN'),
        (100000, 1000000, '100K-1M AZN'),
        (1000000, float('inf'), 'Over 1M AZN')
    ]

    range_counts = []
    range_labels = []
    for min_val, max_val, label in debt_ranges:
        count = len(companies_with_debt[
            (companies_with_debt['debt'] > min_val) &
            (companies_with_debt['debt'] <= max_val)
        ])
        if count > 0:
            range_counts.append(count)
            range_labels.append(label)

    colors2 = sns.color_palette("YlOrRd", len(range_counts))
    bars2 = ax2.barh(range(len(range_counts)), range_counts, color=colors2, alpha=0.8)
    ax2.set_yticks(range(len(range_counts)))
    ax2.set_yticklabels(range_labels, fontsize=10)
    ax2.set_xlabel('Number of Companies', fontsize=12)
    ax2.set_title('Debt Amount Distribution (Companies with Debt)',
                  fontsize=14, fontweight='bold')

    for i, v in enumerate(range_counts):
        ax2.text(v + 5, i, f'{v:,}', va='center', fontsize=10, fontweight='bold')

    ax2.invert_yaxis()
    ax2.set_xlim(0, max(range_counts) * 1.15)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '06_debt_distribution_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 06_debt_distribution_analysis.png")


def chart_7_data_coverage_quality():
    """Data Quality: Regional Coverage Assessment"""
    print("Generating Chart 7: Data Coverage Quality...")

    coverage = summary_df.copy()
    coverage['coverage_status'] = coverage['count'].apply(
        lambda x: 'Complete (50)' if x == 50
        else 'Incomplete (1-49)' if x > 0
        else 'No Data (0)'
    )

    status_counts = coverage['coverage_status'].value_counts()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Coverage status distribution
    colors1 = ['#2ecc71', '#f39c12', '#e74c3c']
    bars1 = ax1.bar(range(len(status_counts)), status_counts.values,
                    color=colors1, alpha=0.8, width=0.6)
    ax1.set_xticks(range(len(status_counts)))
    ax1.set_xticklabels(['Complete\n(50 records)', 'Incomplete\n(1-49 records)', 'No Data\n(0 records)'],
                        fontsize=11)
    ax1.set_ylabel('Number of Regions', fontsize=12)
    ax1.set_title('Data Coverage Status by Region', fontsize=14, fontweight='bold')

    for i, v in enumerate(status_counts.values):
        percentage = (v / len(coverage)) * 100
        ax1.text(i, v + 1, f'{v}\n({percentage:.1f}%)',
                ha='center', fontsize=11, fontweight='bold')

    ax1.set_ylim(0, max(status_counts.values) * 1.15)

    # Incomplete regions detail
    incomplete = coverage[coverage['count'] < 50].sort_values('count', ascending=True).head(15)

    colors2 = ['#e74c3c' if c == 0 else '#f39c12' for c in incomplete['count']]
    bars2 = ax2.barh(range(len(incomplete)), incomplete['count'], color=colors2, alpha=0.8)
    ax2.set_yticks(range(len(incomplete)))
    ax2.set_yticklabels(incomplete['region'], fontsize=9)
    ax2.set_xlabel('Number of Companies', fontsize=12)
    ax2.set_title('Regions with Incomplete Data (Top 15)', fontsize=14, fontweight='bold')

    for i, (idx, row) in enumerate(incomplete.iterrows()):
        ax2.text(row['count'] + 1, i, f"{int(row['count'])}",
                va='center', fontsize=9, fontweight='bold')

    ax2.invert_yaxis()
    ax2.set_xlim(0, 50)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '07_data_coverage_quality.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 07_data_coverage_quality.png")


def chart_8_risk_and_compliance_metrics():
    """Risk Management: Compliance and Risk Indicators"""
    print("Generating Chart 8: Risk and Compliance Metrics...")

    # Calculate risk metrics
    total_companies = len(df)
    metrics = {
        'Active Companies': (df['active'].sum(), '#2ecc71'),
        'VAT Compliant': (df['vatPayer'].sum(), '#3498db'),
        'With Debt': ((df['debt'] > 0).sum(), '#f39c12'),
        'With Sanctions': ((df['sanctions_json'].str.len() > 2).sum(), '#e67e22'),
        'Risky Status': (df['riskyPayer'].sum(), '#c0392b'),
        'Inactive/Stopped': ((df['taxpayerStatus_name_az'] == 'Dayandırılmış').sum(), '#95a5a6')
    }

    fig, ax = plt.subplots(figsize=(14, 7))

    metric_names = list(metrics.keys())
    metric_values = [v[0] for v in metrics.values()]
    metric_colors = [v[1] for v in metrics.values()]
    metric_percentages = [(v / total_companies * 100) for v in metric_values]

    bars = ax.barh(range(len(metrics)), metric_values, color=metric_colors, alpha=0.8)
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels(metric_names, fontsize=12)
    ax.set_xlabel('Number of Companies', fontsize=12)
    ax.set_title('Business Risk and Compliance Profile - Key Indicators',
                 fontsize=14, fontweight='bold')

    # Add value labels with percentages
    for i, (val, pct) in enumerate(zip(metric_values, metric_percentages)):
        ax.text(val + 50, i, f'{val:,} ({pct:.1f}%)',
               va='center', fontsize=11, fontweight='bold')

    ax.set_xlim(0, max(metric_values) * 1.15)
    ax.invert_yaxis()

    # Add total debt annotation
    total_debt = df['debt'].sum()
    ax.text(0.98, 0.02, f'Total Outstanding Debt: {total_debt/1_000_000:.1f}M AZN',
           transform=ax.transAxes, fontsize=11, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
           ha='right', va='bottom')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '08_risk_compliance_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 08_risk_compliance_metrics.png")


def chart_9_charter_capital_distribution():
    """Capital Investment: Charter Capital Analysis"""
    print("Generating Chart 9: Charter Capital Distribution...")

    df_capital = df[df['charterCapital'].notna() & (df['charterCapital'] > 0)].copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Capital ranges
    capital_ranges = [
        (0, 100, 'Under 100 AZN'),
        (100, 1000, '100-1K AZN'),
        (1000, 10000, '1K-10K AZN'),
        (10000, 100000, '10K-100K AZN'),
        (100000, 1000000, '100K-1M AZN'),
        (1000000, float('inf'), 'Over 1M AZN')
    ]

    range_counts = []
    range_labels = []
    for min_val, max_val, label in capital_ranges:
        count = len(df_capital[
            (df_capital['charterCapital'] > min_val) &
            (df_capital['charterCapital'] <= max_val)
        ])
        range_counts.append(count)
        range_labels.append(label)

    colors1 = sns.color_palette("YlGn", len(range_counts))
    bars1 = ax1.barh(range(len(range_counts)), range_counts, color=colors1, alpha=0.8)
    ax1.set_yticks(range(len(range_counts)))
    ax1.set_yticklabels(range_labels, fontsize=10)
    ax1.set_xlabel('Number of Companies', fontsize=12)
    ax1.set_title('Charter Capital Distribution', fontsize=14, fontweight='bold')

    for i, v in enumerate(range_counts):
        if v > 0:
            ax1.text(v + 10, i, f'{v:,}', va='center', fontsize=10, fontweight='bold')

    ax1.invert_yaxis()
    ax1.set_xlim(0, max(range_counts) * 1.15)

    # Top regions by total charter capital
    regional_capital = df_capital.groupby('region')['charterCapital'].sum().sort_values(ascending=False).head(12)
    regional_capital_millions = regional_capital / 1_000_000

    colors2 = sns.color_palette("Greens_r", len(regional_capital_millions))
    bars2 = ax2.barh(range(len(regional_capital_millions)), regional_capital_millions,
                     color=colors2, alpha=0.8)
    ax2.set_yticks(range(len(regional_capital_millions)))
    ax2.set_yticklabels(regional_capital_millions.index, fontsize=10)
    ax2.set_xlabel('Total Charter Capital (Million AZN)', fontsize=12)
    ax2.set_title('Top 12 Regions by Total Charter Capital', fontsize=14, fontweight='bold')

    for i, (region, value) in enumerate(regional_capital_millions.items()):
        ax2.text(value + 15, i, f'{value:.1f}M',
                va='center', fontsize=9, fontweight='bold')

    ax2.invert_yaxis()
    ax2.set_xlim(0, max(regional_capital_millions) * 1.15)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '09_charter_capital_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 09_charter_capital_distribution.png")


def chart_10_regional_business_density():
    """Market Penetration: Regional Business Density"""
    print("Generating Chart 10: Regional Business Density...")

    regional_stats = df.groupby('region').agg({
        'tin': 'count',
        'active': 'sum',
        'vatPayer': 'sum'
    }).reset_index()
    regional_stats.columns = ['region', 'total_companies', 'active_companies', 'vat_companies']
    regional_stats['active_rate'] = (regional_stats['active_companies'] / regional_stats['total_companies'] * 100).round(1)

    # Filter complete regions only
    regional_stats = regional_stats[regional_stats['total_companies'] == 50].sort_values('active_companies', ascending=False).head(20)

    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(regional_stats))
    width = 0.35

    bars1 = ax.bar(x - width/2, regional_stats['active_companies'], width,
                   label='Active Companies', color='#2ecc71', alpha=0.8)
    bars2 = ax.bar(x + width/2, regional_stats['vat_companies'], width,
                   label='VAT Registered', color='#3498db', alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(regional_stats['region'], rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('Number of Companies', fontsize=12)
    ax.set_title('Top 20 Regions by Active Business Density', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)

    # Add activity rate line
    ax2 = ax.twinx()
    ax2.plot(x, regional_stats['active_rate'], 'ro-', linewidth=2, markersize=4,
            label='Activity Rate %', alpha=0.7)
    ax2.set_ylabel('Activity Rate (%)', fontsize=12, color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    ax2.legend(loc='upper right', fontsize=10)
    ax2.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '10_regional_business_density.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 10_regional_business_density.png")


def main():
    """Generate all business insight charts"""
    print("\n" + "="*70)
    print("BUSINESS ANALYTICS CHART GENERATION")
    print("="*70 + "\n")

    chart_1_company_status_overview()
    chart_2_regional_debt_concentration()
    chart_3_organization_type_distribution()
    chart_4_vat_compliance_by_org_type()
    chart_5_company_registration_trends()
    chart_6_debt_distribution_analysis()
    chart_7_data_coverage_quality()
    chart_8_risk_and_compliance_metrics()
    chart_9_charter_capital_distribution()
    chart_10_regional_business_density()

    print("\n" + "="*70)
    print(f"✓ Successfully generated 10 business insight charts in '{CHARTS_DIR}/'")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
