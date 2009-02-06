from django.db import connection

def pop_key():
    """
    <Purpose>
      Returns a new, never used 512 bit public and private key
    <Arguments>
      None
    <Exceptions>
      None
    <Side Effects>
      Deletes the returned key from the keygen.keys_512 table
    <Returns>
      [] if no more keys are available
      [public,private] new key pair
    """
    cursor = connection.cursor()
    cursor.execute("BEGIN")
    cursor.execute("SELECT id,pub,priv FROM keygen.keys_512 limit 1")
    row = cursor.fetchone()
    if row == ():
        cursor.execute("ABORT")
        return []
    cursor.execute("DELETE from keygen.keys_512 WHERE id=%d"%(row[0]))
    cursor.execute("COMMIT")
    return [row[1],row[2]]

