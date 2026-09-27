import os
import argparse
from sqlalchemy import create_engine, MetaData, select, text
from sqlalchemy.orm import Session

def migrate_data(sqlite_url: str, postgres_url: str, dry_run: bool = False):
    print(f"Connecting to Source SQLite: {sqlite_url}")
    source_engine = create_engine(sqlite_url)
    source_meta = MetaData()
    source_meta.reflect(bind=source_engine)
    
    print(f"Connecting to Target PostgreSQL: {postgres_url}")
    target_engine = create_engine(postgres_url)
    target_meta = MetaData()
    # It is expected that Alembic has already been run on target, so schema exists.
    target_meta.reflect(bind=target_engine)
    
    # Sort tables by dependency order (foreign keys)
    sorted_tables = source_meta.sorted_tables
    
    total_migrated = 0
    total_skipped = 0
    
    with source_engine.connect() as src_conn, target_engine.connect() as tgt_conn:
        if not dry_run:
            tgt_conn.execute(text("BEGIN;"))
            # Disable constraints temporarily if possible, though sorted_tables should help.
            
        for table in sorted_tables:
            if table.name not in target_meta.tables:
                print(f"Skipping table {table.name} (not found in target schema)")
                continue
                
            print(f"Migrating table {table.name}...")
            
            # Read all rows
            query = select(table)
            rows = src_conn.execute(query).fetchall()
            
            if not rows:
                print(f"  -> 0 rows")
                continue
                
            filtered_rows = []
            skipped = 0
            
            for row in rows:
                row_dict = dict(row._mapping)
                
                # Filter synthetic data from observations
                if table.name == "observations":
                    if row_dict.get("capture_method") != "LIVE":
                        skipped += 1
                        continue
                
                filtered_rows.append(row_dict)
            
            if filtered_rows:
                target_table = target_meta.tables[table.name]
                if not dry_run:
                    tgt_conn.execute(target_table.insert(), filtered_rows)
                print(f"  -> Migrated {len(filtered_rows)} rows (Skipped {skipped} synthetic)")
                total_migrated += len(filtered_rows)
            else:
                print(f"  -> Migrated 0 rows (Skipped {skipped} synthetic)")
                
            total_skipped += skipped
            
        if not dry_run:
            tgt_conn.execute(text("COMMIT;"))
            print("Migration committed.")
            
    print(f"\n--- MIGRATION SUMMARY ---")
    print(f"Total Rows Migrated: {total_migrated}")
    print(f"Total Synthetic/Invalid Rows Skipped: {total_skipped}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate AeroCPI SQLite data to PostgreSQL")
    parser.add_argument("--sqlite", type=str, default="sqlite:///aerocpi_dev.db", help="SQLite DB URL")
    parser.add_argument("--postgres", type=str, required=True, help="PostgreSQL DB URL")
    parser.add_argument("--dry-run", action="store_true", help="Run without committing")
    args = parser.parse_args()
    
    migrate_data(args.sqlite, args.postgres, args.dry_run)
