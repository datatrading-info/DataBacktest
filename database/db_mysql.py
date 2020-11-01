
import urllib.parse as urlparse
import os, datetime

import MySQLdb as mdb


CREATE_EXCHANGE = """CREATE TABLE `exchange` (
                      `id` int NOT NULL AUTO_INCREMENT,
                      `abbrev` varchar(32) NOT NULL,
                      `name` varchar(255) NOT NULL,
                      `city` varchar(255) NULL,
                      `country` varchar(255) NULL,
                      `currency` varchar(64) NULL,
                      `timezone_offset` time NULL,
                      `created_date` datetime NOT NULL,
                      `last_updated_date` datetime NOT NULL,
                      PRIMARY KEY (`id`)
                    ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
                    """

CREATE_DATA_VENDOR = """CREATE TABLE `data_vendor` (
                          `id` int NOT NULL AUTO_INCREMENT,
                          `name` varchar(64) NOT NULL,
                          `website_url` varchar(255) NULL,
                          `support_email` varchar(255) NULL,
                          `created_date` datetime NOT NULL,
                          `last_updated_date` datetime NOT NULL,
                          PRIMARY KEY (`id`)
                        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
                        """

CREATE_SYMBOL = """CREATE TABLE `symbol` (
                      `id` int NOT NULL AUTO_INCREMENT,
                      `exchange_id` int NULL,
                      `ticker` varchar(32) NOT NULL,
                      `instrument` varchar(64) NOT NULL,
                      `name` varchar(255) NULL,
                      `sector` varchar(255) NULL,
                      `currency` varchar(32) NULL,
                      `created_date` datetime NOT NULL,
                      `last_updated_date` datetime NOT NULL,
                      PRIMARY KEY (`id`),
                      KEY `index_exchange_id` (`exchange_id`)
                    ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
                """

CREATE_DAILY_PRICE = """CREATE TABLE `daily_price` (
                          `id` int NOT NULL AUTO_INCREMENT,
                          `data_vendor_id` int NOT NULL,
                          `symbol_id` int NOT NULL,
                          `price_date` datetime NOT NULL,
                          `created_date` datetime NOT NULL,
                          `last_updated_date` datetime NOT NULL,
                          `open_price` decimal(19,4) NULL,
                          `high_price` decimal(19,4) NULL,
                          `low_price` decimal(19,4) NULL,
                          `close_price` decimal(19,4) NULL,
                          `adj_close_price` decimal(19,4) NULL,
                          `volume` bigint NULL,
                          PRIMARY KEY (`id`),
                          KEY `index_data_vendor_id` (`data_vendor_id`),
                          KEY `index_synbol_id` (`symbol_id`)
                        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
                        """

class DB:
    def __init__(self):
        # Connect to the MySQL instance
        self.db_host = '192.168.1.2'
        self.db_user = 'trading'
        self.db_pass = 'teama4gg'
        self.db_name = 'securities_master'
      #  self.port =

    def conn(self):
        self.connect = mdb.connect(host=self.db_host, user=self.db_user, passwd=self.db_pass, db=self.db_name)
        return self.connect

    def close(self):
        self.connect.commit()
        self.connect.close()



    def createDB(self):

        sql_drop_tables = (
                           '''DROP TABLE exchange;''',
                           '''DROP TABLE data_vendor;''',
                           '''DROP TABLE symbol;''',
                           '''DROP TABLE daily_price;'''
                           )
        for sql in sql_drop_tables:
            try:
                con = self.conn()
                c = con.cursor()
                c.execute(sql)
                con.commit()
                self.close()
            except Exception as error:
                self.close()
                print(error)
                pass

        sql_create_tables = (CREATE_EXCHANGE, CREATE_DATA_VENDOR, CREATE_SYMBOL, CREATE_DAILY_PRICE)
        for sql in sql_create_tables:
            try:
                con = self.conn()
                c = con.cursor()
                c.execute(sql)
                con.commit()
                self.close()
            except Exception as error:
                self.close()
                print(error)
                pass




