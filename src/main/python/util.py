import nepali_datetime

from PySide2.QtCore import Qt


def date_to_str(date):
    """
    Convert nepali_datetime.date object to %Y-%m-%d format
    :param date: nepali_datetime.date object to be formatted
    :return nepali_datetime.date object formatted to string
    """
    return date.strftime("%Y-%m-%d")


def str_to_date(date_string):
    """
    Convert a string in format %Y-%m-%d to nepali_datetime.date object
    :param date_string: date string to be converted
    :return: nepali_datetime.date object
    """
    values = date_string.split('-')
    if len(values) != 3:
        return None
    year, month, day = values
    try:
        year, month, day = int(year), int(month), int(day)
        date = nepali_datetime.date(year, month, day)
    except ValueError:
        return None
    return date


def get_previous_month_date(dt):
    """
    Return a date with month just before the given date's month
    :param dt: nepali_datetime.date object
    :return: date with previous month
    """
    if dt.month - 1 == 0:
        days = nepali_datetime._days_in_month(dt.year - 1, 12)
        return dt.replace(year=dt.year - 1, month=12, day=days)
    else:
        days = nepali_datetime._days_in_month(dt.year, dt.month - 1)
        return dt.replace(month=dt.month - 1, day=days)


def get_next_month_date(dt):
    """
    Return a date with month just after the given date's month
    :param dt: nepali_datetime.date object
    :return: date with next month
    """
    if dt.month + 1 == 12:
        return dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        return dt.replace(month=dt.month + 1, day=1)


def get_month_start(dt):
    """
    Return starting date of the given date's month
    :param dt: nepali_datetime.date object
    :return: starting date of month
    """
    return dt.replace(day=1)


def get_month_end(dt):
    """
    Return ending date of the given date's month
    :param dt: nepali_datetime.date object
    :return: ending date of month
    """
    return dt.replace(day=nepali_datetime._days_in_month(dt.year, dt.month))


def is_date_end_of_month(dt):
    """
    Check if the given date is the last date in the given date's month
    :param dt: nepali_datetime.date object
    :return: True of False, if the given date is the last date in the given date's month
    """
    if dt.day == nepali_datetime._days_in_month(dt.year, dt.month):
        return True
    return False


def table_models_to_excel_sheet(models, excel_sheet):
    """
    Write a table model to given excel sheet
    :param model: table model
    :param excel_file: excel sheet
    """
    total_rows = 1
    for model in models:
        # include header
        rows = model.rowCount(model) + 1
        cols = model.columnCount(model)
        for row in range(rows):
            for col in range(cols + 1):
                if row == 0:
                    # first row is header
                    data = model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                else:
                    # else it is data
                    data = model.data(model.index(row - 1, col), Qt.DisplayRole)
                excel_sheet.cell(column=col + 1, row=total_rows + row,
                                 value=data)
        # increment total rows and columns and add extra space
        total_rows += rows + 1
