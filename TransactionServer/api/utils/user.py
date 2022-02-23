
from api.utils.db import getDb
import time
from api.utils.quoteServer import getQuote
from hashlib import sha256
from pymongo.bson.objectid import ObjectId
from api.utils.db import dbCallWrapper

db, client = getDb()

def getBalance(id):
    id = ObjectId(id)
    return dbCallWrapper({'_id': id}, {'balance': 1}, func = db.user.find_one, eventLog = False)

def addBalance(id, amount):
    id = ObjectId(id)
    return dbCallWrapper({'_id': id}, {'$inc': {'balance': amount}}, func = db.user.update_one, eventLog = True)

def subBalance(id, amount):
    id = ObjectId(id)
    return dbCallWrapper({'_id': id}, {'$inc': {'balance': -amount}}, func = db.user.update_one, eventLog = True)

def getTransactions(id):
    id = ObjectId(id)
    return dbCallWrapper({'_id': id}, {'transactions': 1}, func = db.user.find_one, eventLog = False)

def getAllTransactions():
    return dbCallWrapper({}, {'transactions': 1}, func = db.user.find, eventLog = False)

def getUser(id):
    id = ObjectId(id)
    return dbCallWrapper({"_id": id}, func = db.user.find_one, eventLog = False)

def addTransaction(id, transaction):
    id = ObjectId(id)
    return dbCallWrapper({'_id': id}, {'$push': {'transactions': transaction}}, func = db.user.update_one)


def createUser(name, email, password):
    # email must be unique
    if(db.user.find_one({'email': email})): # don't need to wrap this 
        raise Exception('Email already in use')

    return dbCallWrapper({
        'name': name,
        'email': email,
        'password': sha256(password.encode('utf-8')).hexdigest(),
        'balance': 0.00, 
        'transactions': [], 
        'stocks': [],
        'pending_buy':{},
        'pending_sell':{},
        'triggers': [],
        'pending_triggers': []
        }, func = db.user.insert_one)

def login(email, password):
    user = dbCallWrapper({'email': email, 'password': sha256(password.encode('utf-8')).hexdigest()}, func = db.user.find_one)

    if(user):
        # TODO: generate token, return token
        return user
    else:
        return False

# sets the pending transaction to the pending transaction field on the user
# fails if the user does not have enough balance
def buyStock(id, amount, quote):
    id = ObjectId(id)
    price = quote['price']
    stock = quote['ticker']
    timestamp = quote['timestamp']
    cryptographicKey = quote['cryptographicKey']
    user = getUser(id)
    # check if the user has enough balance to buy
    if(user['balance'] >= amount * price):

        # set pending transaction
        dbCallWrapper({'_id': id}, {
            '$set': {
                'pending_buy' : {
                    'stock': stock, 
                    'amount': amount, 
                    'price': price, 
                    'timestamp': timestamp, 
                    'cryptographicKey': cryptographicKey
                }
            }
        }, db.user.update_one)
        return True
    raise Exception('Insufficient balance')

# removes the pending buy
# adds the transaction to the transactions list
# if the any quote is over 1 minute old, we fail 
def commitBuy(id):
    id = ObjectId(id)
    user = getUser(id)
    transaction = user['pending_transaction']
    if(transaction):
        if(time.time() - transaction['timestamp'] > 60):
            # clear the pending transaction
            db.user.update_one({'_id': id}, {'$set': {'pending_buy': None}})
            raise Exception('Quote expired')
        else:
            # buy the stock
            if(transaction['stock'] in user['stocks'].keys()):
                dbCallWrapper( {'_id': id}, {
                    '$inc': {
                        'stocks.' + transaction['stock'] + '.amount': transaction['amount'],
                        'balance': -transaction['amount'] * transaction['price']
                    }, 
                    '$push':{
                        'stocks.' + transaction['stock'] + 'price': {
                            transaction['amount']: transaction['price']
                        },
                        'transactions': transaction
                    },
                    '$set': {'pending_buy': None}
                }, func = db.user.update_one, eventLog = {'type': 'accountTransaction', 'username': str(id), 'timestamp': int(time.time()), 'action': 'BUY_SHARES', 'stock': transaction['stock'], 'amount': transaction['amount'], 'price': transaction['price'], 'cryptographicKey': transaction['cryptographicKey']})
                
            else:
                dbCallWrapper( {'_id': id}, {
                    '$set': {
                        'stocks.' +transaction['stock']: {
                            'stock': transaction['stock'], 
                            'amount': transaction['amount'], 
                            'price': [
                                {
                                    transaction['amount']: transaction['price']
                                }
                            ]
                        },
                        'pending_buy': None
                    },
                    '$push': {
                        'transactions': transaction
                    },
                    '$inc': {
                        'balance': -transaction['amount'] * transaction['price']
                    }
                }, func = db.user.update_one, eventLog = {'type': 'accountTransaction', 'username': str(id), 'timestamp': int(time.time()), 'action': 'BUY_SHARES', 'stock': transaction['stock'], 'amount': transaction['amount'], 'price': transaction['price'], 'cryptographicKey': transaction['cryptographicKey']})
            
            
            

            return True
    raise Exception('No pending transaction')

def sellStock(id, stock, amount, price, timestamp, cryptographicKey):
    id = ObjectId(id)
    user = getUser(id)
    # check if the user has enough of the stock to sell
    if(stock in user['stocks'].keys() and user['stocks'][stock]['amount'] >= amount):
       
        # set the transaction to the user's pending transaction
        dbCallWrapper(
            {'_id': id}, {
                '$set': {
                    'pending_sell': {
                        'stock': stock, 
                        'amount': amount,
                        'price': price, 
                        'timestamp': timestamp, 
                        'cryptographicKey': cryptographicKey
                    }
                }
            }, 
            func = db.user.update_one,
            eventLog = {'type': 'debugEvent', 'username': str(id), 'timestamp': int(time.time()), 'action': 'SELL', 'stock': stock, 'amount': amount, 'price': price, 'cryptographicKey': cryptographicKey}
        )
        return True
    raise Exception('Insufficient stock')

def commitSell(id):
    id = ObjectId(id)
    user = getUser(id)
    transaction = user['pending_sell']
    if(transaction):
        if(time.time() - transaction['timestamp'] > 60):
            # clear the pending transaction
            dbCallWrapper({'_id': id}, {'$set': {'pending_sell': None}}, func = db.user.update_one)
            raise Exception('Quote expired')
        else:
            # sell the stock
            totalAmount = user['stocks'][transaction['stock']]['amount']

            if(totalAmount == transaction['amount']):
                dbCallWrapper(
                    {'_id': id}, {
                        '$inc': {
                            'stocks.' + transaction['stock'] + '.amount': -transaction['amount'],
                            'balance': transaction['amount'] * transaction['price']
                        },
                        '$push':{
                            'transactions': transaction
                        },
                        '$set': {
                            'pending_sell': None,
                            'stocks.' + transaction['stock']: None
                        }
                    }, 
                    func = db.user.update_one,
                    eventLog = {'type': 'accountTransaction', 'username': str(id), 'timestamp': int(time.time()), 'action': 'SELL_SHARES', 'stock': transaction['stock'], 'amount': transaction['amount'], 'price': transaction['price'], 'cryptographicKey': transaction['cryptographicKey']}
                )
            else:

                dbCallWrapper({'_id': id}, {
                    '$inc': {
                        'stocks.' + transaction['stock'] + '.amount': -transaction['amount'],
                        'balance': transaction['amount'] * transaction['price']
                    },
                    '$push':{
                        'transactions': transaction,
                        'stocks.' + transaction['stock'] + '.price': {
                            -transaction['amount']: transaction['price']
                        }
                    },
                    '$set': {
                        'pending_sell': None
                    }
                }, func = db.user.update_one, eventLog = {'type': 'accountTransaction', 'username': str(id), 'timestamp': int(time.time()), 'action': 'SELL_SHARES', 'stock': transaction['stock'], 'amount': transaction['amount'], 'price': transaction['price'], 'cryptographicKey': transaction['cryptographicKey']})

            return True
    raise Exception('No pending transaction')

def cancelSell(id):
    id = ObjectId(id)
    # clear the pending transaction
    if (getUser(id)['pending_sell']):
        dbCallWrapper({'_id': id}, {'$set': {'pending_sell': None}}, func = db.user.update_one)
        return True
    raise Exception('No pending buy')

def cancelBuy(id):
    id = ObjectId(id)
    # clear the pending transaction
    if (getUser(id)['pending_buy']):
        dbCallWrapper({'_id': id}, {'$set': {'pending_buy': None}}, func = db.user.update_one)
        return True
    raise Exception('No pending buy')


def setBuyAmount(id, stock, amount):
    id = ObjectId(id)
    
    return dbCallWrapper({'_id': id}, {
        '$set': {
            'pendingTrigger': {
                'stock': stock,
                'amount': amount,
                'type': 'buy'
            }
        }
    }, func = db.user.update_one)

def setSellAmount(id, stock, amount):
    id = ObjectId(id)

    return dbCallWrapper({'_id': id}, {
        '$set': {
            'pendingTrigger': {
                'stock': stock,
                'amount': amount,
                'type': 'sell'
            }
        }
    }, func = db.user.update_one)

def setBuyTrigger(id, stock, price):
    id = ObjectId(id)
    
    if(getUser(id)['pendingTrigger']['stock'] == stock and getUser(id)['pendingTrigger']['type'] == 'buy'):
        return dbCallWrapper({'_id': id}, {
            '$set': {
                'pending_trigger': None,
                'triggers': {
                    stock: {
                        'amount': getUser(id)['pendingTrigger']['amount'],
                        'price': price
                    }
                }
            }
        }, func = db.user.update_one)
    raise Exception('No pending trigger')

def setSellTrigger(id, stock, price):
    id = ObjectId(id)

    if(getUser(id)['pendingTrigger']['stock'] == stock and getUser(id)['pendingTrigger']['type'] == 'sell'):
        return dbCallWrapper({'_id': id}, {
            '$set': {
                'pending_trigger': None,
                'sell_triggers': {
                    stock: {
                        'amount': getUser(id)['pendingTrigger']['amount'],
                        'price': price
                    }
                }
            }
        }, func = db.user.update_one)
    raise Exception('No pending trigger')
def cancelSellTrigger(id, stock):
    id = ObjectId(id)
    user = getUser(id)
    if(user['sell_triggers'][stock] and user['triggers'][stock]['type'] == 'sell'):
        return db.user.update_one({'_id': id}, {
            '$set': {
                'triggers.' + stock: None
            }
        })
    raise Exception('No active sell trigger on specified stock')

def cancelBuyTrigger(id, stock):
    id = ObjectId(id)
    user = getUser(id)
    if(user['buy_triggers'][stock] and user['buy_triggers'][stock]['type'] == 'buy'):
        return dbCallWrapper({'_id': id}, {
            '$set': {
                'triggers.' + stock: None
            }
        }, func = db.user.update_one)

def getTriggers():

    return dbCallWrapper({}, {'triggers': 1}, func = db.user.find)
