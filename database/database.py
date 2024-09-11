import pyodbc

class Database:
    def __init__(self, username="test", password="test", host="test", database="test",
                 port="8282") -> pyodbc.Connection:
        self.username = username
        self.password = password
        self.host = host
        self.database = database
        self.port = port

    def _get_username(self):
        return self.username

    def _get_password(self) -> str:
        return self.password

    def _get_host(self) -> str:
        return self.host

    def _get_port(self) -> str:
        return self.port

    def _get_database(self) -> str:
        return self.database

    def connect(self):
        username = self._get_username()
        password = self._get_password()
        host = self._get_host()
        port = self._get_port()
        database = self._get_database()

        config = "DRIVER={ODBC Driver 17 for SQL Server};" + f"SERVER={host},{port};DATABASE={database};UID={username};PWD={password};"
        connection = pyodbc.connect(config)

        return connection