#!/usr/bin/env python3
"""
Data Cleaning and Normalization Script
Fixes region name duplicates and removes duplicate companies
"""

import pandas as pd
import json
from pathlib import Path

def normalize_region_name(region):
    """
    Normalize Azerbaijani region names by standardizing letter encoding.
    Maps various spellings to single canonical form.
    """
    if pd.isna(region):
        return region

    # Define canonical mappings for known duplicate regions
    region_mappings = {
        # Baku variations
        'BAKI': 'BAKİ',

        # Agcabadi variations
        'AĞCABƏDI': 'AĞCABƏDİ',

        # Celilabad variations
        'CƏLILABAD': 'CƏLİLABAD',

        # Fuzuli variations
        'FÜZULI': 'FÜZULİ',

        # Imisli variations
        'İMIŞLI': 'İMİŞLİ',

        # Kurdemir variations
        'KÜRDƏMIR': 'KÜRDƏMİR',

        # Lerik variations
        'LERIK': 'LERİK',

        # Mingecevir variations
        'MINGƏÇEVIR': 'MİNGƏÇEVİR',

        # Pirallahi variations
        'PIRALLAHI': 'PİRALLAHI',

        # Sabirabad variations
        'SABIRABAD': 'SABİRABAD',

        # Seki variations
        'ŞƏKI': 'ŞƏKİ',

        # Sirvan variations
        'ŞIRVAN': 'ŞİRVAN',

        # Siyezen variations
        'SIYƏZƏN': 'SİYƏZƏN',

        # Semkir variations (from summary - zero data regions)
        'ŞƏMKIR': 'ŞƏMKİR',

        # Bilasuvar variations
        'BILƏSUVAR': 'BİLƏSUVAR',
    }

    return region_mappings.get(region, region)


def clean_taxpayer_data():
    """
    Clean the taxpayer dataset:
    1. Normalize region names
    2. Remove duplicate companies (same TIN)
    3. Generate cleaned dataset and statistics
    """

    print("="*70)
    print("DATA CLEANING AND NORMALIZATION")
    print("="*70)

    # Load original data
    print("\n1. Loading original data...")
    df = pd.read_csv('data/taxpayers_all_regions.csv')
    print(f"   Original records: {len(df)}")
    print(f"   Original unique TINs: {df['tin'].nunique()}")
    print(f"   Original regions: {df['region'].nunique()}")

    # Step 1: Normalize region names
    print("\n2. Normalizing region names...")
    df['region_original'] = df['region']
    df['region'] = df['region'].apply(normalize_region_name)

    regions_before = df['region_original'].nunique()
    regions_after = df['region'].nunique()
    print(f"   Regions before normalization: {regions_before}")
    print(f"   Regions after normalization: {regions_after}")
    print(f"   Merged regions: {regions_before - regions_after}")

    # Show what was merged
    print("\n   Region merges performed:")
    merged_regions = df.groupby('region')['region_original'].unique()
    for region, originals in merged_regions.items():
        if len(originals) > 1:
            print(f"   • {region}: merged {list(originals)}")

    # Step 2: Remove duplicate companies (keep first occurrence by TIN)
    print("\n3. Removing duplicate companies (by TIN)...")
    duplicates_before = len(df[df.duplicated(subset=['tin'], keep=False)])
    print(f"   Duplicate records found: {duplicates_before}")

    # Keep first occurrence, drop duplicates
    df_clean = df.drop_duplicates(subset=['tin'], keep='first')

    print(f"   Records after deduplication: {len(df_clean)}")
    print(f"   Unique TINs: {df_clean['tin'].nunique()}")
    print(f"   Duplicate records removed: {len(df) - len(df_clean)}")

    # Step 3: Update summary statistics
    print("\n4. Generating cleaned summary statistics...")
    summary_clean = df_clean.groupby('region').size().reset_index()
    summary_clean.columns = ['region', 'count']
    summary_clean = summary_clean.sort_values('region')

    # Step 4: Save cleaned data
    print("\n5. Saving cleaned datasets...")

    # Drop the temporary original region column
    df_clean = df_clean.drop(columns=['region_original'])

    # Save cleaned full dataset
    df_clean.to_csv('data/taxpayers_all_regions_clean.csv', index=False)
    print(f"   ✓ Saved: data/taxpayers_all_regions_clean.csv ({len(df_clean)} records)")

    # Save cleaned summary
    summary_clean.to_csv('data/taxpayers_all_regions_summary_clean.csv', index=False)
    print(f"   ✓ Saved: data/taxpayers_all_regions_summary_clean.csv ({len(summary_clean)} regions)")

    # Step 5: Generate data quality report
    print("\n6. Generating data quality report...")

    report = {
        'cleaning_date': pd.Timestamp.now().isoformat(),
        'original_stats': {
            'total_records': int(len(df)),
            'unique_tins': int(df['tin'].nunique()),
            'unique_regions': int(df['region_original'].nunique())
        },
        'cleaned_stats': {
            'total_records': int(len(df_clean)),
            'unique_tins': int(df_clean['tin'].nunique()),
            'unique_regions': int(df_clean['region'].nunique())
        },
        'removed': {
            'duplicate_records': int(len(df) - len(df_clean)),
            'merged_regions': int(regions_before - regions_after)
        },
        'merged_region_groups': {}
    }

    # Add merged region details
    for region, originals in merged_regions.items():
        if len(originals) > 1:
            report['merged_region_groups'][region] = list(originals)

    with open('data/data_cleaning_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Saved: data/data_cleaning_report.json")

    # Step 6: Summary statistics
    print("\n" + "="*70)
    print("CLEANING SUMMARY")
    print("="*70)
    print(f"Original Records:        {len(df):,}")
    print(f"Cleaned Records:         {len(df_clean):,}")
    print(f"Duplicates Removed:      {len(df) - len(df_clean):,} ({(len(df) - len(df_clean))/len(df)*100:.1f}%)")
    print(f"\nOriginal Regions:        {regions_before}")
    print(f"Normalized Regions:      {regions_after}")
    print(f"Regions Merged:          {regions_before - regions_after}")
    print(f"\nData Quality Improvement: {(1 - duplicates_before/len(df))*100:.1f}% → 100%")
    print("="*70)

    # Show regional distribution after cleaning
    print("\n7. Regional distribution after cleaning:")
    print("\n   Regions with complete data (50 companies):")
    complete = summary_clean[summary_clean['count'] == 50]
    print(f"   Count: {len(complete)}")

    print("\n   Regions with incomplete data (<50 companies):")
    incomplete = summary_clean[summary_clean['count'] < 50].sort_values('count')
    for _, row in incomplete.iterrows():
        status = "NO DATA" if row['count'] == 0 else f"{row['count']} companies"
        print(f"   • {row['region']}: {status}")

    print("\n" + "="*70)
    print("✓ Data cleaning completed successfully!")
    print("="*70 + "\n")

    return df_clean, summary_clean


if __name__ == "__main__":
    clean_taxpayer_data()
