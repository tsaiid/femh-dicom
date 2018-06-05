import sys
import pandas as pd

def main():
    if len(sys.argv) is not 4:
        print("argv: csv1_path csv2_path output_csv_path")
        sys.exit(1)

    csv1_path = sys.argv[1]
    csv2_path = sys.argv[2]
    output_csv_path = sys.argv[3]

    df_1 = pd.read_csv(csv1_path)
    df_2 = pd.read_csv(csv2_path)

    df_appended = df_1.append(df_2, ignore_index=True)
    df_appended.to_csv(output_csv_path, index=False)

if __name__ == "__main__":
    main()
