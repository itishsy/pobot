from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.types import DATE, VARCHAR, INT, DECIMAL, BIGINT
import efinance as ef
import pandas as pd
import json
from datetime import datetime


with open("config.json", 'r', encoding='utf-8') as load_f:
    load_dict = json.load(load_f)
    host = load_dict['host']
    username = load_dict['username']
    password = load_dict['password']
engine_agu = create_engine('mysql+pymysql://{}:{}@{}/agu'.format(username, password, host))
engine_agu_k_30 = create_engine('mysql+pymysql://{}:{}@{}/agu_k_30'.format(username, password, host))
engine_agu_i_30 = create_engine('mysql+pymysql://{}:{}@{}/agu_m_30'.format(username, password, host))
engine_agu_k_00 = create_engine('mysql+pymysql://{}:{}@{}/agu_k_00'.format(username, password, host))
engine_agu_i_00 = create_engine('mysql+pymysql://{}:{}@{}/agu_m_00'.format(username, password, host))
engine_agu_k_60 = create_engine('mysql+pymysql://{}:{}@{}/agu_k_60'.format(username, password, host))
engine_agu_i_60 = create_engine('mysql+pymysql://{}:{}@{}/agu_m_60'.format(username, password, host))


def init():
    dbs = query('SELECT `SCHEMA_NAME` AS name FROM `information_schema`.`SCHEMATA` WHERE 1=2')
    print(dbs)
    all_dbs = ['agu', 'agu_k_30', 'agu_i_30', 'agu_k_00', 'agu_i_00', 'agu_k_60', 'agu_i_60']
    for name in all_dbs:
        df = dbs[dbs['name'] == name]
        if len(df) < 1:
            create_sql = 'CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;'.format(name)
            execute(create_sql)


def get_engine(table_name='s_all'):
    if table_name is None:
        return engine_agu

    if table_name.find('_') > 0:
        dbtype=table_name.split('_')[0]
        prefix=table_name.split('_')[1]
        if dbtype == 'k':
            if prefix.startswith('00'):
                return engine_agu_k_00
            elif prefix.startswith('60'):
                return engine_agu_k_60
            elif prefix.startswith('30'):
                return engine_agu_k_30
        elif dbtype == 'i':
            if prefix.startswith('00'):
                return engine_agu_i_00
            elif prefix.startswith('60'):
                return engine_agu_i_60
            elif prefix.startswith('30'):
                return engine_agu_i_30
    return engine_agu


def get_table_name(sql):
    sps = sql.split(' ')
    le = len(sps)
    for i in range(le):
        if (sps[i].upper() == 'FROM') | (sps[i].upper() == 'TABLE'):
            table_name = sps[i+1]
            table_name = table_name.replace("`", "")
            return table_name


def insert(df, table_name):
    engine = get_engine(table_name)
    dtypes = get_dtypes(table_name)
    df.to_sql(name=table_name, con=engine, index=False, if_exists='append', dtype=dtypes)


def execute(sql):
    engine = get_engine(get_table_name(sql))
    conn = engine.connect()
    conn.execute(text(sql))
    conn.commit()


def query(sql):
    engine = get_engine(get_table_name(sql))
    conn = engine.connect()
    df = pd.read_sql_query(text(sql), con=conn)
    conn.close()
    engine.dispose()
    return df


def create(table_name):
    if table_name.startswith('k_'):
        create_sql = '''CREATE TABLE IF NOT EXISTS `{}` (
                  `datetime` varchar(20),
                  `open` decimal(6,2),
                  `close` decimal(6,2),
                  `high` decimal(6,2),
                  `low` decimal(6,2),
                  `volume` bigint(20),
                  `cje` bigint(20),
                  `zf` decimal(12,4),
                  `rise` decimal(12,4),
                  `zde` decimal(12,4),
                  `hsl` decimal(12,4),
                  `klt` int(11) DEFAULT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8'''.format(table_name)
    if table_name.startswith('m_'):
        create_sql = '''CREATE TABLE IF NOT EXISTS `{}` (
                  `datetime` varchar(20),
                  `ma5` decimal(12,6),
                  `ma12` decimal(12,6),
                  `ma26` decimal(12,6),
                  `diff` decimal(12,6),
                  `bar` decimal(12,6),
                  `mark` int(11) DEFAULT 0,
                  `single` int(11) DEFAULT 0,
                  `klt` int(11) DEFAULT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8'''.format(table_name)
    engine = get_engine(table_name)
    conn = engine.connect()
    conn.execute(text(create_sql))
    conn.commit()
    engine.dispose()


def get_dtypes(table_name):
    if table_name.startswith('k_'):
        dtypes_k = {'datetime': VARCHAR(20), 'open': DECIMAL, 'close': DECIMAL, 'high': DECIMAL, 'low': DECIMAL,
                    'volume': BIGINT, 'cje': BIGINT, 'zf': DECIMAL, 'rise': DECIMAL, 'zde': DECIMAL, 'hsl': DECIMAL,
                    'klt': INT}
        return dtypes_k


if __name__ == '__main__':
    print('====== database init ======')
    init()