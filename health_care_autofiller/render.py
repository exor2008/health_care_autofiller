import os
import pathlib
import tempfile
from datetime import datetime, timedelta

import openpyxl
import pandas as pd


def get_current_week():
    today = datetime.now()

    match today.weekday():
        case 6:
            delta = 0
        case _:
            delta = today.weekday() + 1

    sunday = today - timedelta(days=delta)
    return [sunday + timedelta(days=i) for i in range(0, 7)]


class Parser:
    def __init__(self, template: pathlib.Path, client_name: str) -> None:
        self.workbook = openpyxl.load_workbook(template)
        self.client_name = client_name
        self.tmpdir = None

    def fill(self):
        days = "EFGHIJK"
        sheet = self.workbook["Sheet1"]
        week = get_current_week()
        for l, d in zip(days, week):
            sheet[f"{l}{6}"].value = d.day

        sheet["G2"].value = week[0].strftime("%m/%d/%y")
        sheet["J2"].value = week[-1].strftime("%m/%d/%y")

        csv = pd.read_excel(
            pathlib.Path("clients", f"{self.client_name}.xlsx"), header=None
        )
        arr = csv.to_numpy()

        # Fill time
        _from = "E8"
        to = "K15"
        for line, row in zip(
            arr[:8, :],
            sheet.iter_rows(
                min_row=sheet[_from].row,
                min_col=sheet[_from].column,
                max_row=sheet[to].row,
                max_col=sheet[to].column,
            ),
        ):
            for val, cell in zip(line, row):
                cell.value = val.strftime("%H:%M")

        # Fill mark signs
        _from = "E16"
        to = "K43"
        for line, row in zip(
            arr[8:, :],
            sheet.iter_rows(
                min_row=sheet[_from].row,
                min_col=sheet[_from].column,
                max_row=sheet[to].row,
                max_col=sheet[to].column,
            ),
        ):
            for val, cell in zip(line, row):
                if val == 1:
                    cell.value = "✔"

        # Fill patient name
        sheet["G3"] = self.client_name

    def save(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        filename = pathlib.Path(
            self.tmpdir.name,
            f"{self.client_name}.xlsx",
        )
        self.workbook.save(filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
        self.tmpdir.cleanup()
