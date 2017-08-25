import numbers
import json
import config as config
import MySQLdb as mdb
from balance_random import Card, Retailer
from  sqlalchemy.sql.expression import func, select
from sqlalchemy import or_
from pprint import pprint

def retrieve_data(con,sql):
    with con:
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows

def execute_sql(con,sql, data):
    with con:
        cur = con.cursor()
        cur.execute(sql, data)
        con.commit()

def retrieve_retailer_list():
    ret_card_lists = []

    con = mdb.connect(host=config.db_host, user=config.db_user, passwd=config.db_pwd, db=config.db_database)
    card_lists = retrieve_data(con, "select retailer from cards group by retailer")

    retailer_list = []
    for row in card_lists:
        if row[0] != "":
            retailer_list.append(row[0])

    return retailer_list


# Retrieve this batch of cards, ordered by attempts
def get_cards_by_attempt(sa_db, limit=None):
    query = sa_db.session.query(Card).filter(Card.balance.is_(None), Card.invalid == 0).order_by(Card.important.desc(),
                                                                                                 Card.attempts)
    if limit:
        query = query.limit(limit)
    return query.all()


# Get retailers for the current batch of cards
def get_retailers_this_batch(sa_db, ids):
    return sa_db.session.query(Retailer).filter(or_(Retailer.gs_id.in_(ids), Retailer.ai_id.in_(ids))).all()


# def parse_gift_cardinfo_from_db(request_id=0):
#     ret_card_lists = []

#     con = mdb.connect(host=config.db_host, user=config.db_user, passwd=config.db_pwd, db=config.db_database)
#     if request_id != 0:
#         where_str = "where request_id={} ".format(request_id)
#     else:
#         where_str = ""

#     sql = "select card_number, pin_code, request_id, attempts, retailer, balance, note, code, locked \
#     from (Select * from cards {} order by attempts limit 1000) as cards ORDER BY rand()".format(where_str)

#     card_lists = retrieve_data(con, sql)

#     for row in card_lists:
#         item = {
#             "giftCardNumber": row[0],
#             "accessNumber": row[1],
#             "request_id": row[2],
#             "attempts": row[3],
#             "retailer": row[4],
#             "balance": row[5],
#             "note": row[6],
#             "code": int(row[7]),
#             "locked": int(row[8]),
#         }

#         ret_card_lists.append(item)

#     return ret_card_lists

def check_page_changes(service_name):
    con = mdb.connect(host=config.db_host, user=config.db_user, passwd=config.db_pwd, db=config.db_database)
    sql = "select retailer from problems where retailer='{0}'".format(service_name,)

    if len(retrieve_data(con, sql)) == 0:
        ret_value = True
    else:
        ret_value = False

    con.close()
    return ret_value

def save_card_locked(conn, card, lock_status):
    update_sql = """UPDATE cards SET locked=%s WHERE card_number=%s and pin_code=%s"""
    execute_sql(conn, update_sql,  (lock_status, card["giftCardNumber"], card["accessNumber"]))

def update_balance(conn, card):
    try:
        attemps = int(card["attempts"])
    except:
        attemps = 0

    attemps = attemps + 1

    update_sql = """UPDATE cards SET balance=%s, note=%s, updated=now(), code=%s, attempts=%s WHERE card_number=%s and pin_code=%s"""
    execute_sql(conn, update_sql,  (card["balance"], card["error_note"], card["code"], attemps, card["giftCardNumber"], card["accessNumber"]))

def save_request(conn, request_id, request_time, response_time, code, error_note):
    insert_sql = """INSERT INTO requests (request_id, request, response, success, error) VALUES (%s, %s, %s, %s, %s) """
    execute_sql(conn, insert_sql,  (request_id, request_time, response_time, code, error_note))

def process_page_changes(conn, card):
    if check_page_changes(card['retailer']) == True:
        insert_sql = """INSERT INTO problems (retailer, note, created) VALUES (%s, %s, now()) """
        execute_sql(conn, insert_sql,  (card['retailer'], card['error_note']))
