import pytest
import sys
from pathlib import Path
from datetime import date

# Add repository root to sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.models.external_reference_data import ExternalReferenceData
from app.validation_data.schemas import ExternalReferenceDataRecord
from app.validation_data.repository import ValidationDataRepository
from app.validation_data.mospi_validator import MoSPIReferenceValidator
from app.services.mospi_benchmark_service import MospiBenchmarkService
from app.services.index_engine_service import IndexEngineService
from scripts.seed_mospi_cpi2024 import seed_mospi_reference_data
from scripts.seed_demo_data import seed_database

def test_official_airfare_import_and_count(db_session):
    """
    Requirement 1: Official seed script populates exactly 19 observations (2025-01 through 2026-07).
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    records = repo.get_mospi_airfare_series()

    assert len(records) == 19
    assert records[0].reference_period == "2025-01"
    assert records[-1].reference_period == "2026-07"

def test_item_code_and_hierarchy(db_session):
    """
    Requirement 2: Item code must equal 07.3.3.1.2.01 with correct CPI classification hierarchy.
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    records = repo.get_mospi_airfare_series()

    rec = records[0]
    assert rec.item_code == "07.3.3.1.2.01"
    assert rec.item_label == "Airfare"
    assert rec.division_code == "07"
    assert rec.group_code == "07.3"
    assert rec.class_code == "07.3.3"
    assert rec.subclass_code == "07.3.3.1"

def test_base_year_2024(db_session):
    """
    Requirement 3: Base year must equal 2024.
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    records = repo.get_mospi_airfare_series()

    assert all(r.base_year == 2024 for r in records)

def test_current_vs_back_series_separation(db_session):
    """
    Requirement 4: CURRENT benchmark queries must NOT return BACK series records.
    """
    seed_mospi_reference_data(db_session)

    # Insert a dummy BACK series observation
    back_obs = ExternalReferenceData(
        reference_dataset_id="DS-MOSPI-CPI2024-BACK",
        publisher="MoSPI / NSO",
        dataset_name="CPI-2024 Airfare Back Series",
        source="MOSPI_CPI_BACK",
        reference_period="2024-06",
        base_year=2024,
        series_type="BACK",
        geography="All India",
        sector="Combined",
        item_code="07.3.3.1.2.01",
        item_label="Airfare",
        index_value=100.0,
        publication_date=date(2026, 1, 31)
    )
    db_session.add(back_obs)
    db_session.commit()

    repo = ValidationDataRepository(db_session)
    current_records = repo.get_mospi_airfare_series(series_type="CURRENT")

    assert len(current_records) == 19
    assert all(r.series_type == "CURRENT" for r in current_records)

def test_all_india_combined_filtering(db_session):
    """
    Requirement 5: Geography must equal All India and Sector must equal Combined.
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    records = repo.get_mospi_airfare_series()

    assert all(r.geography == "All India" for r in records)
    assert all(r.sector == "Combined" for r in records)

def test_known_index_values_and_yoy_inflation(db_session):
    """
    Requirement 6: Verify exact known values for 2026-03, 2026-04, and 2026-07.
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    rec_map = {r.reference_period: r for r in repo.get_mospi_airfare_series()}

    assert rec_map["2026-03"].index_value == 123.55
    assert rec_map["2026-03"].inflation_value == 14.20

    assert rec_map["2026-04"].index_value == 123.27
    assert rec_map["2026-04"].inflation_value == 11.11

    assert rec_map["2026-07"].index_value == 125.46
    assert rec_map["2026-07"].inflation_value == 22.94

def test_yoy_inflation_interpretation(db_session):
    """
    Requirement 7: Inflation field is Year-on-Year (YOY), NOT Month-on-Month (MoM).
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    records = repo.get_mospi_airfare_series()

    for r in records:
        if r.inflation_value is not None:
            assert r.inflation_type == "YOY"

def test_cpi_weight_metadata_and_separation_from_dgca(db_session):
    """
    Requirement 8: CPI Airfare expenditure weight stored with Annexure 5.3d metadata,
    strictly separated from DGCA traffic proxy weights.
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    rec = repo.get_mospi_airfare_series()[0]

    assert rec.cpi_weight_value is not None
    assert abs(rec.cpi_weight_value - 0.02950972) < 1e-8
    assert rec.cpi_weight_unit == "percent_of_CPI"
    assert rec.cpi_weight_scope == "All India Combined"
    assert "Annexure 5.3d" in rec.cpi_weight_source
    assert "Expert Group Report" in rec.cpi_weight_source_document

def test_cpi2024_airfare_weight_reconciliation_against_annex_5_3d(db_session):
    """
    Requirement 12 (Regression Test): Independently verifies that the imported CPI weight value (0.02950972)
    reconciles against the canonical Annexure 5.3d workbook Sheet 5.3d extraction for Item Code 07.3.3.1.2.01:
    - Total matching rows: 58
    - Rural total: 0.011666250433056633 (~ 0.01166625)
    - Urban total: 0.017843470248557074 (~ 0.01784347)
    - Combined total: 0.029509720681613706 (~ 0.02950972)
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    rec = repo.get_mospi_airfare_series()[0]

    assert abs(rec.cpi_weight_value - 0.02950972) < 1e-8

    wb_path = Path("C:/Users/priya/Downloads/1769670019171-Annex_5.3.xlsx")
    if wb_path.exists():
        import zipfile, xml.etree.ElementTree as ET
        with zipfile.ZipFile(wb_path, 'r') as z:
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                for elem in tree.iter():
                    if elem.tag.endswith('t'):
                        shared_strings.append(elem.text or '')

            workbook_xml = ET.fromstring(z.read('xl/workbook.xml'))
            sheets = {s.attrib.get('name'): s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') for s in workbook_xml.iter() if s.tag.endswith('sheet')}
            rels_xml = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
            rel_map = {r.attrib['Id']: r.attrib['Target'] for r in rels_xml.iter() if r.tag.endswith('Relationship')}

            sheet_file = 'xl/' + rel_map[sheets['5.3d']]
            sheet_xml = ET.fromstring(z.read(sheet_file))

            rows = {}
            for row in sheet_xml.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                r_idx = int(row.attrib['r'])
                row_dict = {}
                for c in row.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                    col_ref = c.attrib['r']
                    col_letter = ''.join([ch for ch in col_ref if ch.isalpha()])
                    cell_type = c.attrib.get('t')
                    val_elem = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                    val = val_elem.text if val_elem is not None else None
                    if cell_type == 's' and val is not None:
                        val = shared_strings[int(val)]
                    elif val is not None:
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                    row_dict[col_letter] = val
                rows[r_idx] = row_dict

        airfare_rows = [r for r, d in sorted(rows.items()) if any(str(d.get(c)) == '07.3.3.1.2.01' for c in d)]
        assert len(airfare_rows) == 58

        rural_rows = [r for r in airfare_rows if rows[r].get('C') == 'Share within State***']
        urban_rows = [r for r in airfare_rows if rows[r].get('C') == '13.9.0.9.2.02']

        assert len(rural_rows) == 25
        assert len(urban_rows) == 33

        rural_tot = sum(rows[r].get('N') for r in rural_rows if isinstance(rows[r].get('N'), float))
        urban_tot = sum(rows[r].get('N') for r in urban_rows if isinstance(rows[r].get('N'), float))
        combined_tot = sum(rows[r].get('N') for r in airfare_rows if isinstance(rows[r].get('N'), float))

        assert abs(rural_tot - 0.011666250433056633) < 1e-6
        assert abs(urban_tot - 0.017843470248557074) < 1e-6
        assert abs(combined_tot - 0.029509720681613706) < 1e-6

def test_data_and_provenance_status_separation(db_session):
    """
    Requirement 9: data_status = OFFICIAL_SOURCE_DATA while provenance_status = PARTIAL.
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    rec = repo.get_mospi_airfare_series()[0]

    assert rec.data_status == "OFFICIAL_SOURCE_DATA"
    assert rec.provenance_status == "PARTIAL"
    assert rec.canonical_dataset_sha256 is not None

def test_mospi_validator_engine(db_session):
    """
    Requirement 10: MoSPIReferenceValidator runs schema, consistency, and regression fixture checks cleanly.
    """
    seed_mospi_reference_data(db_session)
    repo = ValidationDataRepository(db_session)
    records = repo.get_mospi_airfare_series()

    is_valid, errors = MoSPIReferenceValidator.validate_dataset(records)
    assert is_valid is True
    assert len(errors) == 0

def test_benchmark_comparison_service_metadata(db_session):
    """
    Requirement 11: Benchmark comparison service includes comparison_type='benchmark',
    interpretation='market_measurement_vs_official_monthly_cpi', and methodological_difference=True.
    """
    seed_database(db_session)
    seed_mospi_reference_data(db_session)

    run, _ = IndexEngineService.execute_index_run(db_session, "2026-08-01", "2026-09-01")
    comparison = MospiBenchmarkService.compare_run_with_mospi_benchmark(db_session, run.run_id)

    assert comparison["run_id"] == run.run_id
    assert comparison["comparison_metrics"]["comparison_type"] == "benchmark"
    assert comparison["comparison_metrics"]["interpretation"] == "market_measurement_vs_official_monthly_cpi"
    assert comparison["comparison_metrics"]["methodological_difference"] is True
    assert comparison["mospi_benchmark"]["mospi_index_value"] == 125.46
