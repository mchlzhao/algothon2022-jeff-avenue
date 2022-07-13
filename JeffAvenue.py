import numpy as np
import pandas as pd

nInst=100
COMMISSION = 0.0025
MAX_DOLLAR_POS = 10000

currentPos = np.zeros(nInst)

def mean_revert(prcSoFar, instr, window=50):
    global currentPos

    prices = prcSoFar[instr, :]
    price_avg = prices[-window-1:-1].mean()

    cur_resid = prices[-1] / price_avg - 1
    if cur_resid == np.nan:
        return

    prev_pos = currentPos[instr]

    multiplier = 1
    if prev_pos <= 0 and cur_resid < -COMMISSION * multiplier:
        currentPos[instr] = MAX_DOLLAR_POS / prices[-1]
    elif prev_pos >= 0 and cur_resid > COMMISSION * multiplier:
        currentPos[instr] = -MAX_DOLLAR_POS / prices[-1]

def pair_mean_revert(prcSoFar, instr1, instr2, window=50):
    global currentPos

    prices1 = prcSoFar[instr1, :]
    prices2 = prcSoFar[instr2, :]

    diff = prices1 - prices2
    mean_diff = diff[-window-1:-1].mean()
    cur_prem = (diff[-1] - mean_diff) / (prices1[-1] + prices2[-1])

    prev_pos = currentPos[instr1]
    pos1 = min(MAX_DOLLAR_POS / prices1[-1],
        MAX_DOLLAR_POS / prices2[-1])

    multiplier = 2
    if prev_pos <= 0 and cur_prem < -COMMISSION * multiplier:
        currentPos[instr1] = pos1
        currentPos[instr2] = -pos1
    elif prev_pos >= 0 and cur_prem > COMMISSION * multiplier:
        currentPos[instr1] = -pos1
        currentPos[instr2] = pos1

def pair_mean_revert_ratio(prcSoFar, instr1, instr2, window=50):
    global currentPos

    prices1 = prcSoFar[instr1, :]
    prices2 = prcSoFar[instr2, :]

    ratio = prices1 / prices2
    mean_ratio = ratio[-window-1:-1].mean()
    cur_prem = ratio[-1] / mean_ratio - 1

    prev_pos = currentPos[instr1]

    multiplier = 2
    if prev_pos <= 0 and cur_prem < -COMMISSION * multiplier:
        currentPos[instr1] = MAX_DOLLAR_POS / prices1[-1]
        currentPos[instr2] = -MAX_DOLLAR_POS / prices2[-1]
    elif prev_pos >= 0 and cur_prem > COMMISSION * multiplier:
        currentPos[instr1] = -MAX_DOLLAR_POS / prices1[-1]
        currentPos[instr2] = MAX_DOLLAR_POS / prices2[-1]


try_list = [0,8,9,38,63,88,98]

def ewma_trade(data):
    global currentPos
    
    df = pd.DataFrame(data.transpose(), columns = ['price_'+str(x) for x in range(0,100)])
    
    if len(df) < 30:
        return 0
    for i in range(0,100):
        df['ema_dd_'+str(i)] = (df['price_'+str(i)].ewm(halflife = 20).mean() - 
            df['price_'+str(i)].ewm(halflife = 5).mean()).diff()
    position = identify_trades(df)
    for i in try_list:
        currentPos[i] = position[i]

def identify_trades(data):
    position_flag = [[0 for j in range(len(data))] for i in range(100)]
    position = [[0 for j in range(len(data))] for i in range(100)]
    timer = [[0 for j in range(len(data))] for i in range(100)]
    for index, row in data[30:].iterrows():
        for i in try_list:
            limit = data['ema_dd_'+str(i)].std()*2
            position_flag[i][index] = position_flag[i][index-1]
            position[i][index] = position[i][index-1]
            if position_flag[i][index-1] == 0:
                if row['ema_dd_'+str(i)] > limit:
                    position_flag[i][index] = 1
                    position[i][index] = round(9500/row['price_'+str(i)])
                    timer[i][index] = 20
                elif row['ema_dd_'+str(i)]< -limit:
                    position_flag[i][index] = -1
                    position[i][index] = -round(9500/row['price_'+str(i)])
                    timer[i][index] = 20
            elif position_flag[i][index-1] == 1:
                if timer[i][index-1] != 0:
                    timer[i][index] = timer[i][index-1] - 1
                elif row['ema_dd_'+str(i)]< 0:
                    position_flag[i][index] = 0
                    position[i][index] = 0
            else:
                if timer[i][index-1] != 0:
                    timer[i][index] = timer[i][index-1] - 1
                elif row['ema_dd_'+str(i)]> -0:
                    position_flag[i][index] = 0
                    position[i][index] = 0
    final_position = [position[i][len(data)-1] for i in range(100)]
    return final_position


def getMyPosition (prcSoFar):
    global currentPos

    _, nt = prcSoFar.shape

    window = 50
    if nt < window:
        return currentPos

    singles = [35, 90]
    for x in singles:
        mean_revert(prcSoFar, x)
    pairs = [(25, 69), (43, 66), (45, 61), (50, 55), (67, 71)]
    # (45, 61) and (67, 71) are questionable
    for x, y in pairs:
        pair_mean_revert(prcSoFar, x, y)
    ratio_pairs = [(5, 65), (1, 10)]
    for x, y in ratio_pairs:
        pair_mean_revert_ratio(prcSoFar, x, y)
    # mean_revert(prcSoFar, 35)
    # pair_mean_revert(prcSoFar, 12, 90)
    # pair_mean_revert_ratio(prcSoFar, 58, 63)
    ewma_trade(prcSoFar)
    
    return currentPos
