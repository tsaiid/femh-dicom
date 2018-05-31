import sys
import pandas as pd

def main():
    if len(sys.argv) is not 4:
        print("argv: all_csv_path target_csv_path output_csv_path")
        sys.exit(1)

    all_csv_path = sys.argv[1]
    target_csv_path = sys.argv[2]
    output_csv_path = sys.argv[3]

    df_a = pd.read_csv(all_csv_path)
    df_t = pd.read_csv(target_csv_path)

    df_cleaned = df_t[df_t.ACCNO.isin(df_a.ACCNO)].sort_values(by='ACCNO')
    df_cleaned.to_csv(output_csv_path, index=False)

if __name__ == "__main__":
    main()
