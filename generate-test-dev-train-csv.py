import sys
import pandas as pd

def main():
    if len(sys.argv) is not 4:
        print("argv: pos_csv_path neg_csv_path category")
        sys.exit(1)

    pos_csv_path = sys.argv[1]
    neg_csv_path = sys.argv[2]
    category = sys.argv[3]

    df_pos = pd.read_csv(pos_csv_path)
    df_neg = pd.read_csv(neg_csv_path)

    pos_len = len(df_pos)
    pos_test_len = round( pos_len * 0.1 )
    pos_dev_len = round( (pos_len - pos_test_len) * 0.2 )
    pos_train_len = pos_len - pos_test_len - pos_dev_len

    neg_len = len(df_neg)
    neg_test_len = round( neg_len * 0.1 )
    neg_dev_len = round( (neg_len - neg_test_len) * 0.2 )
    neg_train_len = neg_len - neg_test_len - neg_dev_len

    df_pos = df_pos[['ACCNO']]
    df_neg = df_neg[['ACCNO']]
    df_pos['ACCNO'] = df_pos['ACCNO'] + '.png'
    df_neg['ACCNO'] = df_neg['ACCNO'] + '.png'

    df_pos.columns = ['Image Index']
    df_neg.columns = ['Image Index']

    df_pos[category] = 1
    df_neg[category] = 0

    df_pos = df_pos.sample(frac=1)
    df_neg = df_neg.sample(frac=1)

    df_pos_test = df_pos[:pos_test_len]
    df_pos_dev = df_pos[pos_test_len:pos_test_len+pos_dev_len]
    df_pos_train = df_pos[pos_test_len+pos_dev_len:]

    df_neg_test = df_neg[:neg_test_len]
    df_neg_dev = df_neg[neg_test_len:neg_test_len+neg_dev_len]
    df_neg_train = df_neg[neg_test_len+neg_dev_len:]

    df_test = df_pos_test.append(df_neg_test, ignore_index=True)
    df_dev = df_pos_dev.append(df_neg_dev, ignore_index=True)
    df_train = df_pos_train.append(df_neg_train, ignore_index=True)

    #test_path = 'test-{}.csv'.format(category)
    #dev_path = 'dev-{}.csv'.format(category)
    #train_path = 'train-{}.csv'.format(category)
    test_path = 'test.csv'
    dev_path = 'dev.csv'
    train_path = 'train.csv'

    df_test.to_csv(test_path, index=False)
    df_dev.to_csv(dev_path, index=False)
    df_train.to_csv(train_path, index=False)


if __name__ == "__main__":
    main()
