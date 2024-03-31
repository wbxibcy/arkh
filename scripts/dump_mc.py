import sqlite3
import pandas as pd

# ---- database ops ----

def connect(sqlite_file):
    ''' Connects to an SQLite database file '''
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    return conn, c

def total_rows(cursor, table_name, print_out=False):
    ''' Returns the total number of rows in the database '''
    cursor.execute('SELECT COUNT(*) FROM {}'.format(table_name))
    count = cursor.fetchall()
    if print_out:
        print('\nTotal rows: {}'.format(count[0][0]))
    return count[0][0]

def table_col_info(cursor, table_name, print_out=False):
    '''
       Returns a list of tuples with column informations:
      (id, name, type, notnull, default_value, primary_key)

    '''
    cursor.execute('PRAGMA TABLE_INFO({})'.format(table_name))
    info = cursor.fetchall()

    if print_out:
        print("\nColumn Info:\nID, Name, Type, NotNull, DefaultVal, PrimaryKey")
        for col in info:
            print(col)
    return info

def values_in_col(cursor, table_name, print_out=True):
    ''' Returns a dictionary with columns as keys and the number of not-null
        entries as associated values.
    '''
    cursor.execute('PRAGMA TABLE_INFO({})'.format(table_name))
    info = cursor.fetchall()
    col_dict = dict()
    for col in info:
        col_dict[col[1]] = 0
    for col in col_dict:
        cursor.execute('SELECT ({0}) FROM {1} WHERE {0} IS NOT NULL'.format(col, table_name))
        # In my case this approach resulted in a better performance than using COUNT
        number_rows = len(cursor.fetchall())
        col_dict[col] = number_rows
    if print_out:
        print("\nNumber of entries per column:")
        for i in col_dict.items():
            print('{}: {}'.format(i[0], i[1]))
    return col_dict

def make_char_table(cursor, table_name, id_column, data_frame):
    ''' Builds a character table '''
    cursor.execute('DROP TABLE IF EXISTS {tn}'.format(tn=table_name))
    cursor.execute('CREATE TABLE {tn} ({idf} {ft} PRIMARY KEY)'\
        .format(tn=table_name, idf=id_column, ft='INTEGER'))

    cols = data_frame.columns
    nrow = data_frame[id_column].count()
    for i in range(nrow):
        try:
            cursor.execute("INSERT INTO {tn} ({idf}) VALUES (?)"\
                .format(tn=table_name, idf=id_column), (i+1,))
        except sqlite3.IntegrityError:
            print('ERROR: ID already exists in PRIMARY KEY column {}'.format(id_column))
    conn.commit()

    for column_name in cols:
        if not column_name == id_column:
            cursor.execute("ALTER TABLE {tn} ADD COLUMN {cn} {ct} NOT NULL DEFAULT ''"\
                .format(tn=table_name, cn=column_name, ct='TEXT'))
            vals = data_frame[column_name].fillna('')
            for i in range(nrow):
                cursor.execute("UPDATE {tn} SET {cn}=(?) WHERE {idf}=(?)"\
                    .format(tn=table_name, cn=column_name, idf=id_column), (vals[i], i+1))
            conn.commit()


if __name__ == '__main__':
    # Creates a table of characters
    sqlite_file = '../instance/project.db'
    table_name = 'mc_char'
    id_column = '字序'

    text_file = 'guangyun'

    data = pd.read_csv(text_file, delimiter='\t', na_values='', encoding='utf-8')
    conn, c = connect(sqlite_file)
    make_char_table(c, table_name, id_column, data)
    conn.close()

    # View info
    conn, c = connect(sqlite_file)
    total_rows(c, table_name, print_out=True)
    table_col_info(c, table_name, print_out=True)
    values_in_col(c, table_name, print_out=True)
    conn.close()
