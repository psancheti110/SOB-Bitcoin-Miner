# PRATEEK SANCHETI
# At the end of my programe, I was able to get a valid block with a fee sum of 5,801,519 with the total weight less than max_block_weight i.e. 4,000,000 
import pandas as pd
import heapq

#reading the .csv file, aking a dataframe of it to use in the code
df = pd.read_csv('mempool.csv')
file1 = open("block.txt","a")

#Making new colums in the read data frame, 
df['F/W'] = 0 # Density (Fee/Weight), 
df['hash_val'] = 0 # A column that'll just keep a check of the transactions included in the final block
df['fee_new'] = df['fee'] # making a copy of fee column so that no mess up happens to the orignal values
df['weight_new'] = df['weight'] # making a copy of weight column so that no mess up happens to the orignal values

# parent fee function, takes in a row and its index as parameters,
# this function updates the value of fee_new, weight_new and F/W column of the dataframe and substitues with cumulative sum for fee and weight for all the parents txns of a particular txn. It is a recursive function.  
def parent_fee(row, index):
    if(row['F/W']!=0):
        return row
    else:
        if(pd.isna(row['parents '])):
            return row
        else:
            parents = row['parents ']
            parents_split = parents.split(';')
            for parent_ids in parents_split:
                # recursive call made for each of the parent
                my_list = parent_fee(df[df['tx_id']==parent_ids].iloc[0],df[df['tx_id']==parent_ids].index[0])
                df.loc[index,'fee_new'] = my_list.fee_new 
                df.loc[index,'weight_new'] = my_list.weight_new
                df.loc[index,'F/W'] = row['fee_new']/row['weight_new']
            return df[df['tx_id']==row.tx_id].iloc[0]

# going over the dataframe to call parent_fee function for them
for index,row in df.iterrows():
    if(pd.isna(row['parents '])):
        row['F/W'] = row['fee_new']/row['weight_new']
        df.loc[index,'F/W'] = row['F/W']
    else:
        my_row = parent_fee(df.loc[index], index)


# Making a heap based on F/W, weight_new fro the df
pq_list =[]
for index,row in df.iterrows():
    pq_list.append([-1*row['F/W'], -1*row['weight_new'], row['tx_id']])
heapq.heapify(pq_list)

# check_parent function takes in a row of df as a parameter
# this function checks until which parent is not visited while including in the block. and returns new cumulative fee, weight, f/w values up till that txn 

def check_parent(row):
    if(row.hash_val!=0):
        return 0,0
    if(pd.isna(row['parents '])):
        return row.fee, row.weight
    cur_fee = row.fee
    cur_weight = row.weight
    parents = row['parents ']
    parents_split = parents.split(';')
    for parent_ids in parents_split:
        ret_val_fee, ret_val_weight = check_parent(df[df['tx_id']==parent_ids].iloc[0])
        cur_fee += ret_val_fee
        cur_weight += ret_val_weight
    return cur_fee, cur_weight

tx_id_array = []
# mark_hash func takes in row and its index as parameters.
# this function is called after check_parent and checking weather the weight after including this txn will be less than max_block_weight. 
# this func marks all the parents for a particular txn recursively and adds the txn in block.txt file
def mark_hash(row, index):
    if(row.hash_val==1):
        return
    else:
        if(pd.isna(row['parents '])):
            df.loc[index, 'hash_val'] = 1
        else:
            parents = row['parents ']
            parents_split = parents.split(';')
            for parent_ids in parents_split:
                mark_hash(df[df['tx_id']==parent_ids].iloc[0], df[df['tx_id']==parent_ids].index[0])
            df.loc[index, 'hash_val'] = 1
        file1.write(row.tx_id)
        file1.write("\n") 
        tx_id_array.append(row.tx_id)


fee_sum=0
weight_sum=0
# popping one txn at a time, gives the txn with max F/W val i.e. highest density. and so fee goes up more as compared to weight.
# Calling check_parent and mark_hash if the conditions are satisfies for all the txn in the heap. 
while(len(pq_list)!=0):
    a = heapq.heappop(pq_list)
    row = df[df['tx_id']==a[2]].iloc[0]
    if(row.hash_val):
        pass
    else:
        fee, weight = check_parent(row)
        # in case the new F/W value is greater or equal to the orignal, the txn is included. Otherwise it is pushed back into the heap. 
        if(fee/weight >= -1*a[0]): 
            if(weight_sum+weight <= 4000000):
                weight_sum +=weight
                fee_sum += fee
                mark_hash(row, df[df['tx_id']==a[2]].index[0])
        else:    
            heapq.heappush(pq_list, [-1*(fee/weight), -1*weight, row.tx_id])

file1.close()