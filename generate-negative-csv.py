import sys
import pandas as pd

def main():
    if len(sys.argv) is not 4:
        print("argv: all_csv_path pos_csv_path neg_csv_path")
        sys.exit(1)

    all_csv_path = sys.argv[1]
    pos_csv_path = sys.argv[2]
    neg_csv_path = sys.argv[3]

    df_all = pd.read_csv(all_csv_path)
    df_pos = pd.read_csv(pos_csv_path)

    output_size = len(df_pos) * 7 // 3

    df_neg = df_all[~df_all.ACCNO.isin(df_pos.ACCNO)].sample(frac=1)
    df_neg[:output_size].to_csv(neg_csv_path, index=False)


if __name__ == "__main__":
    main()
