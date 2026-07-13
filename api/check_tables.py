import jaydebeapi
conn = jaydebeapi.connect('com.ibm.as400.access.AS400JDBCDriver', 'jdbc:as400://192.168.0.240', ['AYUDATX', 'MXTAC23'])
cursor = conn.cursor()
sql = "SELECT TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = 'TESTLIB' AND (TABLE_NAME LIKE '%USER%' OR TABLE_NAME LIKE '%USUA%' OR TABLE_NAME LIKE '%LOGIN%' OR TABLE_NAME LIKE '%SESION%' OR TABLE_NAME LIKE '%PASS%' OR TABLE_NAME LIKE '%ROL%') ORDER BY TABLE_NAME"
cursor.execute(sql)
for row in cursor.fetchall():
    print(row[0])
cursor.close()
conn.close()
