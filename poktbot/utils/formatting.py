from poktbot.config import get_config
from bokeh.models import ColumnDataSource, DataTable, TableColumn
from bokeh.io import export_png

import tempfile
import os
import pandas as pd


def format_date(date_object):
    """
    Formats the given datetime object into the configuration timezone and date format string.

    :param date_object:
        Datetime object UTC located.

    :returns:
        String date time with the configuration timezone and date formats.
    """
    config = get_config()

    timezone = config['CONF.timezone']
    date_format = config['CONF.date_format']

    if date_object is not None:
        if hasattr(date_object, "dt"):
            date_object = date_object.dt

        date_object = date_object.tz_convert(timezone)

        if hasattr(date_object, "dt"):
            date_object = date_object.dt

        date_object = date_object.strftime(date_format)

    return date_object


# TODO: I encourage changing this export method to not rely on a web browser, which is a cumbersome solution.\
#  The matplotlib solution would be faster.
def df_to_png_bytes(df):
    """
    Exports a dataframe to png byte array.
    """
    if type(df) is pd.Series:
        df = df.to_frame().T

    columns = [TableColumn(field=Ci, title=Ci) for Ci in df.columns]  # bokeh columns
    data_table = DataTable(columns=columns, source=ColumnDataSource(df))  # bokeh table

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = os.path.join(tmp_dir, "image.png")
        export_png(data_table, filename=tmp_file)
        with open(tmp_file, "rb") as f:
            png_bytes = f.read()

    return png_bytes


def df_to_xlsx(df, output_file, sheet_name, index=False, na_rep="NaN"):
    """
    Writes the dataframe into the specified output.

    This function respects the width of each column based on the max length of the contained values.

    :param df:
        DataFrame to store.

    :param output_file:
        Output file to store. Can be a filename or a buffer object.

    :param sheet_name:
        Name of the sheet to store the data into.

    :param index:
        Boolean flag specifying if the index should be stored or not in the excel file.

    :param na_rep:
        Representation for NaN values in the excel.
    """
    writer = pd.ExcelWriter(output_file)
    df.to_excel(writer, sheet_name=sheet_name, index=index, na_rep=na_rep)

    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        writer.sheets[sheet_name].set_column(col_idx, col_idx, column_length)

    writer.save()
