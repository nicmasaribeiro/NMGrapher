"""Numeric CSV/TSV datasets; no expression execution or server-side file storage."""
import csv
import io
import re
import keyword
from dataclasses import dataclass
import numpy as np
from notation import normalize_notation

MAX_DATASETS = 8
MAX_ROWS = 10000
MAX_COLUMNS = 32
MAX_CELLS = 50000
MAX_IMPORT_BYTES = 1024 * 1024

class DatasetError(ValueError):
    pass

class DataColumn(np.ndarray):
    """A sequence of observations, distinct from an algebraic vector."""

@dataclass
class PointSeries:
    x: np.ndarray
    y: np.ndarray


def numeric(cell, decimal='.'):
    cell = cell.strip()
    if not cell: return None
    try:
        v = float(cell.replace(',', '.') if decimal == ',' else cell)
    except ValueError:
        raise DatasetError('Not a number.') from None
    if not np.isfinite(v) or abs(v) > 1e100: raise DatasetError('Use finite numbers within ±1e100.')
    return v


def suggested_name(label, index, used):
    name = re.sub(r'\W+', '_', normalize_notation(label.strip()), flags=re.UNICODE).strip('_')[:40]
    if not name or not name.isidentifier() or keyword.iskeyword(name): name = 'column_' + str(index+1)
    base = name; suffix = 2
    while name in used:
        name = base[:35] + '_' + str(suffix); suffix += 1
    used.add(name)
    return name


def parse_delimited(text, delimiter='auto', header=True, decimal='.'):
    if not isinstance(text, str) or len(text.encode('utf-8')) > MAX_IMPORT_BYTES:
        raise DatasetError('Import up to 1 MB of UTF-8 CSV or TSV text.')
    if delimiter not in ('auto', ',', ';', '\t') or type(header) is not bool or decimal not in ('.', ','):
        raise DatasetError('Choose a supported delimiter, header option, and decimal separator.')
    text = text.lstrip('\ufeff')
    if not text.strip(): raise DatasetError('The dataset is empty.')
    if delimiter == 'auto':
        try: delimiter = csv.Sniffer().sniff(text[:10000], delimiters=',;\t').delimiter
        except csv.Error: delimiter = ','
    if delimiter == decimal: raise DatasetError('Use semicolon or tab delimiters when decimals use a comma.')
    rows = []
    try:
        reader = csv.reader(io.StringIO(text, newline=''), delimiter=delimiter, strict=True)
        for record in reader:
            if not record or all(not c.strip() for c in record): continue
            if len(record) > MAX_COLUMNS: raise DatasetError('Import at most 32 columns.')
            if rows and len(record) != len(rows[0]): raise DatasetError(f'CSV line {reader.line_num} has {len(record)} columns; expected {len(rows[0])}.')
            rows.append(record)
            if len(rows) > MAX_ROWS + int(header) or len(rows)*len(record) > MAX_CELLS + MAX_COLUMNS:
                raise DatasetError('Import at most 10,000 rows and 50,000 cells.')
    except csv.Error as exc:
        raise DatasetError('Invalid CSV quoting or field size: ' + str(exc)) from exc
    if not rows: raise DatasetError('The dataset contains no values.')
    labels = rows.pop(0) if header and rows else [f'column_{i+1}' for i in range(len(rows[0]))]
    if not rows: raise DatasetError('There are no data rows after the header.')
    if len(rows)*len(labels) > MAX_CELLS: raise DatasetError('Import at most 50,000 cells.')
    used = set(); columns = []
    for index, label in enumerate(labels):
        values = []; invalid = 0; missing = 0
        for row in rows:
            try: value = numeric(row[index], decimal)
            except DatasetError: value = None; invalid += 1
            if not row[index].strip(): missing += 1
            values.append(value)
        columns.append({'label':label[:120] or f'Column {index+1}', 'name':suggested_name(label,index,used),
                        'values':values, 'invalid':invalid, 'missing':missing,
                        'numeric':invalid == 0 and any(v is not None for v in values)})
    return {'columns':columns, 'rows':len(rows), 'delimiter':delimiter,
            'preview':[[cell[:120] for cell in row] for row in rows[:8]]}


def identifier(value):
    if not isinstance(value,str) or not 1 <= len(value) <= 80: raise DatasetError('Use a dataset/column name of 1–80 characters.')
    value = normalize_notation(value.strip())
    if not value.isidentifier() or keyword.iskeyword(value): raise DatasetError('Dataset and column names must be valid variable names.')
    return value


def validate_datasets(items, reserved=()):
    if not isinstance(items,list) or len(items)>MAX_DATASETS: raise DatasetError('Use at most 8 datasets.')
    normalized=[]; bindings={}; names=set(); ids=set(); total=0
    for item in items:
        if not isinstance(item,dict): raise DatasetError('Invalid dataset object.')
        name=identifier(item.get('name')); ident=item.get('id')
        if not isinstance(ident,str) or not 1<=len(ident)<=80 or ident in ids: raise DatasetError('Dataset IDs must be unique.')
        if name in names: raise DatasetError('Dataset names must be unique after Greek/notation conversion.')
        ids.add(ident);names.add(name)
        columns=item.get('columns')
        if not isinstance(columns,list) or not 1<=len(columns)<=MAX_COLUMNS: raise DatasetError('Use 1–32 numeric columns per dataset.')
        clean=[]; keys=set(); length=None
        for col in columns:
            if not isinstance(col,dict): raise DatasetError('Invalid dataset column.')
            key=identifier(col.get('name'));binding=name+'_'+key
            if key in keys or binding in bindings or binding in reserved: raise DatasetError(f'Duplicate or reserved dataset column: {binding}')
            keys.add(key); values=col.get('values')
            if not isinstance(values,list) or not 1<=len(values)<=MAX_ROWS: raise DatasetError('Columns need 1–10,000 values.')
            if length is not None and len(values)!=length: raise DatasetError('Dataset columns must have the same number of rows.')
            length=len(values);total+=length
            if total>MAX_CELLS: raise DatasetError('Keep the worksheet within 50,000 dataset cells in total.')
            if any(v is not None and (type(v) not in (int,float) or abs(v)>1e100 or not np.isfinite(v)) for v in values):
                raise DatasetError('Dataset values must be finite real numbers or null for missing cells.')
            if not any(v is not None for v in values):raise DatasetError(f'Column {key} contains no numeric values.')
            label=col.get('label',key)
            if not isinstance(label,str) or len(label)>120: raise DatasetError('Column labels must be text up to 120 characters.')
            clean.append({'name':key,'label':label,'values':values})
            bindings[binding]=np.asarray([np.nan if v is None else v for v in values],dtype=float).view(DataColumn)
        x=item.get('x'); y=item.get('y',[clean[-1]['name']])
        if x is not None: x=identifier(x)
        if not isinstance(y,list) or not y or len(y)>8 or any(not isinstance(v,str) for v in y):raise DatasetError('Choose 1–8 Y columns.')
        y=[identifier(v) for v in y]
        if (x is not None and x not in keys) or len(set(y))!=len(y) or any(v not in keys for v in y):raise DatasetError('Plot columns must belong to this dataset.')
        style=item.get('style','markers')
        if style not in ('markers','lines','lines+markers'):raise DatasetError('Choose points, lines, or lines with points.')
        visible=item.get('visible',True)
        if type(visible) is not bool:raise DatasetError('Dataset visibility must be true or false.')
        normalized.append({'id':ident,'name':name,'columns':clean,'x':x,'y':y,'style':style,'visible':visible})
    return normalized,bindings


def sequence(a):
    a=np.asarray(a)
    if a.ndim!=1 or not 1<=a.size<=MAX_ROWS:raise DatasetError('Use a one-dimensional sequence with 1–10,000 values.')
    return a


def points(x,y):
    x,y=sequence(x),sequence(y)
    if x.shape!=y.shape:raise DatasetError('Point X and Y columns must have equal lengths.')
    if np.any(np.imag(x)!=0):raise DatasetError('Point X values must be real.')
    return PointSeries(x.real,y)


def interpolate(t,x,y):
    x,y=sequence(x),sequence(y)
    if x.shape!=y.shape or x.size<2 or np.any(np.imag(x)!=0) or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)) or not np.all(np.diff(x.real)>0):
        raise DatasetError('interp needs equal-length finite columns and at least two strictly increasing real X values.')
    if np.any(np.imag(t)!=0):raise DatasetError('Interpolation inputs must be real.')
    return np.interp(np.real(t),x.real,y,left=np.nan,right=np.nan)

FUNCTIONS={'points':points,'interp':interpolate,
           'dropna':lambda a:sequence(a)[np.isfinite(a)].view(DataColumn),
           'count':lambda a:int(np.count_nonzero(np.isfinite(a))),
           'median':np.median,'std':np.std,'variance':np.var}
