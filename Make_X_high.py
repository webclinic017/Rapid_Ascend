import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import warnings
from sklearn.preprocessing import MinMaxScaler
warnings.filterwarnings("ignore")
pd.set_option('display.max_rows', 500)

Scaler = MinMaxScaler()

home_dir = os.path.expanduser('~')
dir = home_dir + '/OneDrive/CoinBot/ohlcv/'
ohlcv_list = os.listdir(dir)


def min_max_scaler(price):
    Scaler = MinMaxScaler()
    Scaler.fit(price)

    return Scaler.transform(price)


def made_x(file, input_data_length, Range_fluc, get_fig):

    ohlcv_excel = pd.read_excel(dir + file, index_col=0)
    ohlcv_excel['MA60'] = ohlcv_excel['close'].rolling(60).mean()
    # 현재 포인트가 최저점 (10개의 데이터 중) 이면, 1 / 0
    # 현재 포인트가 최저점 (앞 10개의 뒤 10개 데이터 중) 이면, 1 / 0
    ohlcv_excel['high_check'] = np.where((ohlcv_excel['high'].rolling(10).max() == ohlcv_excel['high'])
                                        & (ohlcv_excel['high'].shift(-9).rolling(10).max() == ohlcv_excel['high']), 1, 0)
    # ohlcv_excel['prev_max'] = ohlcv_excel['high'].rolling(10).max()
    # ohlcv_excel['follow_max'] = ohlcv_excel['high'].shift(-9).rolling(10).max()

    # ----------- dataX, dataY 추출하기 -----------#
    # print(ohlcv_excel.iloc[:, 2:])
    # quit()

    # NaN 제외하고 데이터 자르기 (데이터가 PIXEL 로 들어간다고 생각하면 된다)
    # MA60 부터 FLUC_CLOSE, 존재하는 값만 슬라이싱
    ohlcv_data = ohlcv_excel.values[ohlcv_excel['MA60'].isnull().sum():-9].astype(np.float)
    # print(pd.DataFrame(ohlcv_data).info())
    # print(list(map(float, ohlcv_data[0])))
    # print(ohlcv_data)
    # quit()

    # 결측 데이터 제외
    if len(ohlcv_data) != 0:

        # ----- 데이터 전처리 -----#
        price = ohlcv_data[:, :4]
        volume = ohlcv_data[:, [4]]
        MA60 = ohlcv_data[:, [5]]
        high_check = ohlcv_data[:, [6]]

        scaled_price = min_max_scaler(price)
        scaled_volume = min_max_scaler(volume)
        scaled_MA60 = min_max_scaler(MA60)
        # print(scaled_MA60.shape)

        x = np.concatenate((scaled_price, scaled_volume, scaled_MA60), axis=1)  # axis=1, 세로로 합친다
        y = high_check
        # print(x.shape, y.shape)  # (258, 6) (258, 1)
        # quit()

        dataX = []  # input_data length 만큼 담을 dataX 그릇
        dataY = []  # Target 을 담을 그릇

        for i in range(input_data_length + 1, len(y)):
            # group_x >> 이전 완성된 데이터를 사용해보도록 한다. (진입하는 시점은 데이터가 완성되어있지 않으니까)
            group_x = x[i - 1 - input_data_length: i - 1]  # 0 부터 len(y) - 2 까지 대입
            group_y = y[i]
            # print(group_x.shape)  # (28, 6)
            # print(group_y.shape)  # (1,)
            # quit()
            # if i is input_data_length + 1:
            #     print(group_x, "->", group_y)
            #     quit()
            dataX.append(group_x)  # dataX 리스트에 추가
            dataY.append(group_y)  # dataY 리스트에 추가

        sliced_ohlcv = ohlcv_data[input_data_length + 1:, :-1]

        # ----------- FLUC_CLOSE TO SPAN, 넘겨주기 위해서 INDEX 를 담아주어야 한다. -----------#
        if get_fig == 1:
            spanlist = []
            for m in range(len(ohlcv_excel['fluc_close'])):
                if ohlcv_excel['fluc_close'].iloc[m] > Range_fluc:
                    if m + 1 < len(ohlcv_excel):
                        spanlist.append((m, m + 1))
                    else:
                        spanlist.append((m - 1, m))

            # ----------- 인덱스 초기화 됨 -----------#

            # ----------- Chart 그리기 -----------#
            plt.plot(min_max_scaler(ohlcv_data[:, 1:2]), 'r', label='close')
            plt.plot(scaled_MA60, 'b', label='MA60')
            plt.legend(loc='upper right')

            # Spanning
            for i in range(len(spanlist)):
                plt.axvspan(spanlist[i][0], spanlist[i][1], facecolor='blue', alpha=0.3)

            Date = file.split()[0]
            Coin = file.split()[1].split('.')[0]
            plt.savefig('./Figure_fluc/%s %s.png' % (Date, Coin), dpi=500)
            plt.close()
            # plt.show()
            # ----------- Chart 그리기 -----------#

        return dataX, dataY, sliced_ohlcv


if __name__ == '__main__':

    for i in range(3, 4):

        # ----------- Params -----------#
        input_data_length = 6 * (i ** 2)
        Range_fluc = 1.035  # >> Best Param 을 찾도록 한다.
        get_fig = 0

        Made_X = []
        Made_Y = []

        for file in ohlcv_list:

            result = made_x(file, input_data_length, Range_fluc, get_fig)

            # ------------ 데이터가 있으면 dataX, dataY 병합하기 ------------#
            if result is not None:

                Made_X += result[0]
                Made_Y += result[1]

                # SAVING X, Y
                X = np.array(Made_X)
                Y = np.array(Made_Y)
                np.save('./Made_X_high/Made_X %s' % input_data_length, X)
                np.save('./Made_X_high/Made_Y %s' % input_data_length, Y)

                # 누적 데이터량 표시
                print(file, len(Made_X))  # 현재까지 321927개
                # if len(Made_X) > 100000:
                #     quit()

        plt.plot(Made_Y)
        plt.savefig('./Figure_fluc/high/Made_Y %s.png' % input_data_length)
        plt.close()
