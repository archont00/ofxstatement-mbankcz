import csv
from datetime import datetime
from typing import Iterable, Optional, List
from decimal import Decimal

from ofxstatement import statement
from ofxstatement.statement import StatementLine
from ofxstatement.plugin import Plugin
from ofxstatement.parser import CsvStatementParser


class MBankParser(CsvStatementParser):
    date_format = "%d-%m-%Y"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, *kwargs)
        self.columns = None
        self.mappings = {}

    def split_records(self) -> Iterable[str]:
        """
        Parse metadata scattered around the actual transaction lines and return
        those for further processing.
        """
        reading_records = False
        last_meta_header = None
        records = []
        for line in csv.reader(self.fin, delimiter=";", quotechar='"'):
            if len(line) == 0:
                pass
            elif len(line) == 9 and line[6] == "#Konečný zůstatek:":
                self.statement.end_balance = \
                    Decimal(line[7]
                            .replace(self.statement.currency, "")
                            .replace(" ", "")
                            .replace(",", "."))
                reading_records = False
            elif reading_records:
                records.append(line)
            elif last_meta_header is not None:
                if last_meta_header == "#Měna účtu:":
                    self.statement.currency = line[0]
                elif last_meta_header == "#Číslo účtu:":
                    self.statement.bank_id = line[0].split("/")[1]
                    self.statement.account_id = line[0].split("/")[0]
                elif last_meta_header == "#Za období":
                    self.statement.start_date = datetime.strptime(
                        line[0], '%d.%m.%Y')
                    self.statement.end_date = datetime.strptime(
                        line[1], '%d.%m.%Y')
                last_meta_header = None
            elif len(line) == 2:
                last_meta_header = line[0]
            elif len(line) == 9 and line[6] == "#Počáteční zůstatek:":
                self.statement.start_balance = \
                    Decimal(line[7]
                            .replace(self.statement.currency, "")
                            .replace(" ", "")
                            .replace(",", "."))
                reading_records = True
        return records

    def parse_record(self, line: List[str]) -> Optional[StatementLine]:
        """Parse given transaction line and return StatementLine object"""

        # First line of CSV file contains headers, not an actual transaction
        if self.cur_record == 1:
            # Prepare columns headers lookup table for parsing
            self.columns = {v: i for i, v in enumerate(line)}
            self.mappings = {
                "date": self.columns["#Datum uskutečnění transakce"],
                "memo": self.columns["#Zpráva pro příjemce"],
                "payee": self.columns["#Plátce/Příjemce"],
                "amount": self.columns["#Částka transakce"],
                "check_no": self.columns["#VS"],
            }
            # And skip further processing by parser
            return None

        # Shortcut
        columns = self.columns

        # Normalize string
        for i, v in enumerate(line):
            # Replace colon with space - causes string formatting problems
            line[i] = v.replace(":"," ")
            # Remove leading and trailing spaces 
            line[i] = v.strip()
            # Replace multiple spaces with just one
            line[i] = " ".join(v.split())

        if line[columns["#Částka transakce"]] == "":
            line[columns["#Částka transakce"]] = "0"

        statement_line = super().parse_record(line)

        if line[columns["#Datum uskutečnění transakce"]]:
            statement_line.date_user = line[columns["#Datum uskutečnění transakce"]]
            statement_line.date_user = datetime.strptime(
                statement_line.date_user, self.date_format
            )

        statement_line.id = statement.generate_transaction_id(statement_line)

        # If payee is empty or transactions is percentual saving set payee to -
        if line[columns["#Plátce/Příjemce"]] =="" or line[columns["#Plátce/Příjemce"]
        ].startswith("PLATBA KARTOU Z ČÁSTKY") or line[columns["#Plátce/Příjemce"]
        ].startswith("VÝBĚR Z BANKOMATU Z ČÁSTKY"):
            statement_line.payee = "-"
        elif line[columns["#Číslo účtu plátce/příjemce"]] != "":
            statement_line.payee += "|ÚČ: " + line[columns["#Číslo účtu plátce/příjemce"]]

        # Manually set some of the known transaction types
        payment_type = line[columns["#Popis transakce"]]
        if payment_type.startswith("ZÚČTOVÁNÍ ÚROKŮ"):
            statement_line.trntype = "DEBIT"
        elif payment_type.startswith("PŘIPSÁNÍ ÚROKŮ"):
            statement_line.trntype = "INT"
        elif payment_type.startswith("POPLATEK"):
            statement_line.trntype = "FEE"
        elif payment_type.startswith("ODCHOZÍ"):
            statement_line.trntype = "XFER"
        elif payment_type.startswith("PŘÍCHOZÍ"):
            statement_line.trntype = "XFER"
        elif payment_type.startswith("POS VRÁCENÍ ZBOŽÍ"):
            statement_line.trntype = "XFER"
        elif payment_type.startswith("PŘEDDEF. ODCHOZÍ"):
            statement_line.trntype = "XFER"
        elif payment_type.startswith("VLASTNÍ PŘEVOD"): 
            statement_line.trntype = "XFER"
        elif payment_type.startswith("PŘEVOD NA"):
            statement_line.trntype = "XFER"
        elif payment_type.startswith("VÝBĚR Z BANKOMATU"):
            statement_line.trntype = "ATM"
        elif payment_type.startswith("PLATBA KARTOU"):
            statement_line.trntype = "POS"
        elif payment_type.startswith("INKASO"):
            statement_line.trntype = "DIRECTDEBIT"
        else:
            print(
                'WARN: Unexpected type of payment appeared - "{}". Using OTHER transaction type instead'.format(
                    payment_type
                )
            )
            statement_line.trntype = "OTHER"

        if line[columns["#Zpráva pro příjemce"]] != "":
            statement_line.memo = line[columns["#Zpráva pro příjemce"]]

        if not self.empty_or_null(line[columns["#VS"]]):
            statement_line.memo += "|VS: " + line[columns["#VS"]]

        if not self.empty_or_null(line[columns["#KS"]]):
            statement_line.memo += "|KS: " + line[columns["#KS"]]

        if not self.empty_or_null(line[columns["#SS"]]):
            statement_line.memo += "|SS: " + line[columns["#SS"]]

        if statement_line.amount == 0:
            return None

        return statement_line

    @staticmethod
    def empty_or_null(value: str) -> bool:
        return value in ["", "0"]


class MBankCZPlugin(Plugin):
    """mBank S.A. (Czech Republic) (CSV, cp1250)"""

    def get_parser(self, filename: str) -> MBankParser:
        MBankCZPlugin.encoding = self.settings.get("charset", "cp1250")
        file = open(filename, "r", encoding=MBankCZPlugin.encoding)
        parser = MBankParser(file)
        parser.statement.currency = self.settings.get("currency", "CZK")
        parser.statement.bank_id = self.settings.get("bank", "BREXCZPP")
        parser.statement.account_id = self.settings.get("account", "")
        parser.statement.account_type = self.settings.get("account_type", "CHECKING")
        parser.statement.trntype = "OTHER"
        return parser
